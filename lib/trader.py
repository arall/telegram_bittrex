#!/usr/bin/env python

from lib.bittrex import bittrex
from secrets import BITTREX_KEY, BITTREX_SECRET, DEMO, TRADE, SAFE_ORDER
import datetime


class Trader:
    signal = None
    api = None
    bot = None

    def __init__(self, signal, bot=None):
        self.signal = signal
        self.bot = bot
        self.api = bittrex(BITTREX_KEY, BITTREX_SECRET)
        self.current_price = self.get_last_price()

    # Analises the signal and perform the necessary market orders
    def process(self):
        # Bittrex API error (probably a 5xx error)
        if not self.current_price:
            self.message('Bittrex: price error!')
            return

        # Calculate the target price
        target = self.calc_target_price()
        self.log(
            'Current: %s | Bought: %s | Target: %s'
            % (
                format(self.current_price, '.8f'),
                format(self.signal.b_price, '.8f'),
                format(target, '.8f')
            )
        )

        # Update the signal with the current / highest / lowest prices
        self.prices_update()

        # Bought signals
        if self.signal.status == 3:
            # Profit sell (current price higher or equal to the target)
            if self.current_price >= target:
                self.log('Profit!')
                self.sell()
                return

            # Stop loss sell (current price lower or equal to the stop loss)
            if self.signal.stop_loss and self.current_price <= float(self.signal.stop_loss):
                self.log('Stop loss reached!')
                self.sell()
                return

        # Buy or Sell open orders
        elif self.signal.status == 2 or self.signal.status == 4:
            # Check the order status
            order = self.api.getorder(self.signal.uuid)
            print order
            if order['IsOpen'] is not True:
                # Update the order
                self.processed(order)
                return

    # Get the last market price
    def get_last_price(self):
        try:
            summary = self.api.getmarketsummary(self.signal.market)
            return float(summary[0]['Last'])
        except:
            pass

    # Calculate the target price
    def calc_target_price(self):
        # Percentage
        if self.signal.win_percent is not None:
            return float(self.signal.b_price) + ((
                float(self.signal.win_percent) *
                float(self.signal.b_price)
            ) / 100)
        # Amount
        else:
            return self.signal.win_price

    # Calculate the price to sell
    # (current price - SAFE ORDER %, for faster processing)
    def calc_sell_price(self):
        return float(self.current_price) - ((
                    float(SAFE_ORDER) *
                    float(self.current_price)
                ) / 100)

    # Create a buy order
    def buy(self):
        # stop loss protection
        if self.signal.stop_loss and self.current_price <= float(self.signal.stop_loss):
            self.message('Can\'t buy, stop loss reached (%s)' % format(self.current_price, '.8f'))
            return

        if DEMO:
            return self.buy_update()

        # Places the order
        quantity = self.signal.btc / self.current_price
        order = self.api.buylimit(
            self.signal.market,
            quantity,
            self.current_price
        )

        # Possible API errors
        try:
            order['uuid']
        except:
            self.message('API Error: %s' % order)
            return

        # Updates the order
        self.buy_update(order)

    # Create a sell order
    def sell(self):
        # Reduces the sell price for faster processing
        sell_price = self.calc_sell_price()
        self.log('Adjusted sell price: %s' % format(sell_price, '.8f'))

        if DEMO:
            return self.sell_update()

        # Places the order
        order = self.api.selllimit(
            self.signal.market,
            self.signal.quantity,
            sell_price
        )

        # Possible API errors
        try:
            order['uuid']
        except:
            self.message('API Error: %s' % order)
            return

        # Updates the order
        self.sell_update(order)

    # Mark the order as processed
    def processed(self, order):
        # Buy order
        if order['Type'] == 'LIMIT_BUY':
            self.signal.status = 3
        # Sell order
        else:
            self.signal.status = 5
        self.signal.save()

    # Updates a completed buy order
    def buy_update(self, order=None):
        # Real order
        if order:
            quantity = order['Quantity']
            price = order['PricePerUnit']
            comission = order['CommissionPaid']
            status = 2
            uuid = order['uuid']

        # Demo order
        else:
            price = self.current_price
            quantity = self.signal.btc / self.current_price
            comission = 0
            status = 3
            uuid = 'DEMO'

        self.signal.quantity = quantity
        self.signal.b_price = price
        self.signal.b_uuid = uuid
        self.signal.b_comision = comission
        self.signal.b_date = datetime.datetime.now()
        self.signal.status = status
        self.signal.save()

        # Message
        self.message(
            'Bought %s %s at %s for %s %s' %
            (
                quantity,
                self.signal.coin,
                format(price, '.8f'),
                self.signal.btc,
                TRADE
            )
        )

    # Updates a completed sell order
    def sell_update(self, order=None):
        # Real order
        if order:
            price = order['PricePerUnit']
            comission = order['CommissionPaid']
            status = 4
            uuid = order['uuid']

        # Demo order
        else:
            price = self.calc_sell_price()
            comission = 0
            status = 5
            uuid = 'DEMO'

        self.signal.s_price = price
        self.signal.s_uuid = uuid
        self.signal.s_comision = round(comission, 8)
        self.signal.s_date = datetime.datetime.now()
        self.signal.status = status

        # Profit
        price_change = float(self.signal.s_price) - float(self.signal.b_price)
        self.signal.profit_btc = (price_change * float(self.signal.quantity))
        top = float(self.signal.b_price) - float(self.signal.s_price)
        bottom = float(self.signal.b_price) + float(self.signal.s_price)
        bottom = bottom / 2
        total = top / bottom * 100
        if float(self.signal.b_price) > float(self.signal.s_price):
            total = -abs(total)
        else:
            total = abs(total)
        self.signal.profit_percent = round(total, 8)
        self.signal.save()

        # Message
        self.message(
            'Sold %s %s at %s for %s %s (%s %% profit!)' %
            (
                self.signal.quantity,
                self.signal.coin,
                format(price, '.8f'),
                self.signal.btc,
                TRADE,
                round(self.signal.profit_percent, 2),
            )
        )

    # Update the signal with the current / highest / lowest prices
    def prices_update(self):
        highest_price = self.signal.highest_price
        if highest_price < self.current_price or highest_price is None:
            self.signal.highest_price = self.current_price

        lowest_price = self.signal.lowest_price
        if lowest_price > self.current_price or lowest_price is None:
            self.signal.lowest_price = self.current_price

        self.signal.current_price = self.current_price
        self.signal.save()

    # Shows a console log message
    def log(self, text):
        print '[%d][%s] %s' % (self.signal.id, self.signal.market, text)

    # Sends a telegram message
    def message(self, text):
        if self.bot:
            try:
                self.bot.send_message(self.signal.chat_id, text)
            except Exception as e:
                self.log('Telegram error: %s' % str(e))
                self.log('Message: %s' % text)
        print text
