#!/usr/bin/env python

import telebot
import string
from secrets import TELEGRAM_TOKEN, TRADE, USERNAMES
from lib.trader import Trader
from lib.database import Signal

# Default help message
HELP = 'Use /buy COIN BTC_AMOUNT WIN_RATIO [STOP_LOSS]\n' \
        '/buy DOGE 0.01 5% 0.00000001'


class Message:
    message = None
    signal = None
    text = ''
    coin = ''
    btc = 0
    win_percent = 0
    win_price = None
    stop_loss = None

    def __init__(self, message):
        self.message = message
        self.text = self.message.text.encode('unicode_escape')

    def process(self):
        if self.decode():
            self.create()
            return self.signal

    # Decode the received /buy message
    def decode(self):
        try:
            parts = string.split(self.text, ' ')
            # Coin code
            self.coin = parts[1]
            # Amount of BTC's
            self.btc = round(float(parts[2]), 8)
            # Sell at certain % or amount
            win = parts[3]
            if '%' in win:
                self.win_percent = int(win.replace('%', ''))
            else:
                self.win_price = round(float(win), 8)
            # Stop loss
            if len(parts) > 4:
                self.stop_loss = round(float(parts[4]), 8)

            return True
        except Exception:
            bot.reply_to(self.message, 'I don\'t understand you.\n' + HELP)

    # Create the signal Model
    def create(self):
        # Only authorised usernames
        if self.message.from_user.username not in USERNAMES:
            bot.reply_to(self.message, 'Your nickname is not authorised!')
            return
        self.signal = Signal.create(
            chat_id=self.message.chat.id,
            username=self.message.from_user.username,
            text=self.text,
            coin=self.coin,
            market=TRADE + '-' + self.coin,
            btc=self.btc,
            win_percent=self.win_percent,
            win_price=self.win_price,
            stop_loss=self.stop_loss,
            status=1
        )


bot = telebot.TeleBot(TELEGRAM_TOKEN)


# Buy command
@bot.message_handler(commands=['buy'])
def send_welcome(message):
    message = Message(message)
    signal = message.process()
    if signal:
        trader = Trader(signal, bot)
        trader.buy()


# Default message
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    print 'test'
    bot.reply_to(message, HELP)


bot.polling()
