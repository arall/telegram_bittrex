#!/usr/bin/env python

import telebot
import string
from secrets import TELEGRAM_TOKEN, TRADE, USERNAMES, DEFAULT_AMOUNT, DEFAULT_WIN, DEFAULT_STOPLOSS
from lib.trader import Trader
from lib.database import Signal
import urllib
import time

# Default help message
HELP = 'Use /command COIN [BTC_AMOUNT] [WIN_RATIO] [STOP_LOSS]\n' \
        '/auto DOGE 0.01 5% 0.00000001\n' \
        '/sell COIN' \
        '/buy COIN 0.01' \
        '/status'


class Message:
    message = None
    signal = None
    text = ''
    coin = ''
    btc = DEFAULT_AMOUNT
    win_percent = DEFAULT_WIN
    win_price = None
    stop_loss = None
    stop_loss_percent = DEFAULT_STOPLOSS

    def __init__(self, message):
        self.message = message
        self.text = self.message.text.encode('unicode_escape')

    def process_auto(self):
        if self.decode():
            self.create()
            if self.signal:
                trader = Trader(self.signal, bot)
                trader.buy()

    def process_status(self):
        signals = Signal.select().where(Signal.status.between(2, 4))
        if signals:
            for signal in signals:
                trader = Trader(signal, bot)
                trader.load()
                trader.status()

    def process_buy(self):
        if self.decode():
            self.create(False)
            if self.signal:
                trader = Trader(self.signal, bot)
                trader.buy()

    def process_sell(self):
        if self.decode():
            try:
                self.signal = Signal.select(). \
                    where(Signal.status == 3). \
                    where(Signal.coin == self.coin). \
                    get()
            except:
                bot.reply_to(self.message, 'Coin not found!')
            if self.signal:
                trader = Trader(self.signal, bot)
                trader.sell()

    # Decode the received /buy or /sell message
    def decode(self):
        try:
            parts = string.split(self.text, ' ')
            # Coin code
            self.coin = parts[1]
            # Amount of BTC's
            try:
                self.btc = round(float(parts[2]), 8)
            except:
                pass
            # Sell at certain % or amount
            try:
                win = parts[3]
                if '%' in win:
                    self.win_percent = int(win.replace('%', ''))
                else:
                    self.win_price = round(float(win), 8)
            except:
                pass
            # Stop loss
            try:
                stoploss = parts[4]
                if '%' in stoploss:
                    self.stop_loss_percent = int(stoploss.replace('%', ''))
                else:
                    self.stop_loss = round(float(stoploss), 8)
            except:
                pass

            return True
        except Exception:
            bot.reply_to(self.message, 'I don\'t understand you.\n' + HELP)

    # Create the signal Model
    def create(self, auto=True):
        # Only authorised usernames
        if self.message.from_user.username not in USERNAMES:
            bot.reply_to(self.message, 'Your nickname is not authorised!')
            return
        self.signal = Signal.create(
            chat_id=self.message.chat.id,
            username=self.message.from_user.username,
            text=self.text,
            auto=auto,
            coin=self.coin,
            market=TRADE + '-' + self.coin,
            btc=self.btc,
            win_percent=self.win_percent,
            win_price=self.win_price,
            stop_loss=self.stop_loss,
            stop_loss_percent=self.stop_loss_percent,
            status=1
        )


bot = telebot.TeleBot(TELEGRAM_TOKEN)


@bot.message_handler(commands=['auto'])
def send_auto(message):
    message = Message(message)
    message.process_auto()


@bot.message_handler(commands=['buy'])
def send_buy(message):
    message = Message(message)
    message.process_buy()


@bot.message_handler(commands=['sell'])
def send_sell(message):
    message = Message(message)
    message.process_sell()


@bot.message_handler(commands=['status'])
def send_status(message):
    message = Message(message)
    message.process_status()


# Default message
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    print 'test'
    bot.reply_to(message, HELP)


try:
    bot.polling(none_stop=True)
except urllib.error.HTTPError:
    time.sleep(10)


while True:
    time.sleep(20)
