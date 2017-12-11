#!/usr/bin/env python

import time
import telebot
from secrets import TELEGRAM_TOKEN, INTERVAL
from lib.trader import Trader
from lib.database import Signal

bot = telebot.TeleBot(TELEGRAM_TOKEN)


while True:
    # Select non-finished orders
    signals = Signal.select().where(Signal.status.between(2, 4))
    print signals
    if signals:
        for signal in signals:
            trader = Trader(signal, bot)
            trader.process()
    print 'All jobs executed!'
    time.sleep(INTERVAL)
