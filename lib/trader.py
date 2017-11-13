#!/usr/bin/env python

import time
from lib.bittrex import bittrex
from secrets import BITTREX_KEY, BITTREX_SECRET, DEMO, TRADE
import datetime

ORDER_DELAY = 5


class Trader:
    signal = None
    api = None
    bot = None

    def __init__(self, signal, bot=None):
        self.signal = signal
        self.bot = bot
        self.api = bittrex(BITTREX_KEY, BITTREX_SECRET)
        self.current_price = self.get_last_price()

    def process(self):
        if not self.current_price:
            self.message('Bittrex: price error!')
            return
        target = self.calc_winning_price()
        self.log(
            'Current: %s | Bought: %s | Target: %s'
            % (format(self.current_price, '.8f'), self.signal.b_price, format(target, '.8f'))
        )

        self.nothing_update()

        # Sell for profit
        if self.current_price >= target:
            self.log('Profit!')
            self.sell()
            return

        # Sell for stop loss
        if self.signal.stop_loss and self.current_price <= float(self.signal.stop_loss):
            self.log('Stop loss reached!')
            self.sell()
            return

    def get_last_price(self):
        try:
            summary = self.api.getmarketsummary(self.signal.market)
            return float(summary[0]['Last'])
        except:
            pass

    def calc_winning_price(self):
        if self.signal.win_percent is not None:
            return float(self.signal.b_price) + ((float(self.signal.win_percent) * float(self.signal.b_price)) / 100)
        else:
            return self.signal.win_price

    def buy(self):
        # stop loss protection
        if self.signal.stop_loss and self.current_price <= float(self.signal.stop_loss):
            self.message('Can\'t buy, stop loss reached (%s)' % format(self.current_price, '.8f'))
            return
        if DEMO:
            return self.buy_update()
        quantity = (float(self.signal.quantity) / float(self.current_price))
        order = self.api.buylimit(
            self.signal.market,
            quantity,
            self.current_price
        )
        uuid = order['uuid']
        self.wait_order(uuid)
        self.buy_update(uuid)

    def sell(self):
        if DEMO:
            return self.sell_update()
        order = self.api.selllimit(
            self.signal.market,
            self.signal.quantity,
            self.current_price
        )
        uuid = order['uuid']
        self.wait_order(uuid)
        self.sell_update(uuid)

    def wait_order(self, uuid):
        while True:
            status = self.api.getorder(uuid)
            if status['IsOpen'] is True:
                self.log('Waiting order %s' % uuid)
                time.sleep(ORDER_DELAY)
            else:
                return

    def buy_update(self, uuid=None):
        if uuid:
            order = self.api.getorder(uuid)
            quantity = order['Quantity']
            price = order['PricePerUnit']
            comission = order['CommissionPaid']
        else:
            price = self.current_price
            quantity = self.signal.btc / self.current_price
            comission = 0

        self.signal.quantity = quantity
        self.signal.b_price = price
        self.signal.b_uuid = uuid
        self.signal.b_comision = comission
        self.signal.b_date = datetime.datetime.now()
        self.signal.status = 2
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

    def sell_update(self, uuid=None):
        if uuid:
            order = self.api.getorder(uuid)
            price = order['PricePerUnit']
            comission = order['CommissionPaid']
        else:
            price = self.current_price
            comission = 0

        self.signal.s_price = price
        self.signal.s_uuid = uuid
        self.signal.s_comision = round(comission, 8)
        self.signal.s_date = datetime.datetime.now()
        self.signal.status = 3

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

    def nothing_update(self):
        highest_price = self.signal.highest_price
        if highest_price < self.current_price or highest_price is None:
            self.signal.highest_price = self.current_price

        lowest_price = self.signal.lowest_price
        if lowest_price > self.current_price or lowest_price is None:
            self.signal.lowest_price = self.current_price

        self.signal.current_price = self.current_price
        self.signal.save()

    def log(self, text):
        print '[%d][%s] %s' % (self.signal.id, self.signal.market, text)

    def message(self, text):
        if self.bot:
            self.bot.send_message(self.signal.chat_id, text)
        print text
