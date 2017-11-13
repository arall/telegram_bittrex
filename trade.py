#!/usr/bin/env python

import time
from threading import Thread
from Queue import Queue
import telebot
from secrets import TELEGRAM_TOKEN
from lib.trader import Trader
from lib.database import Signal

INTERVAL = 60
CONCURRENT = 10

bot = telebot.TeleBot(TELEGRAM_TOKEN)


def analysis():
    signal = q.get()
    trade = Trader(signal, bot)
    trade.process()
    q.task_done()


# Daemon
q = Queue(CONCURRENT * 2)
for i in range(CONCURRENT):
    t = Thread(target=analysis)
    t.daemon = True
    t.start()

while True:
    signals = Signal.select().where(Signal.status == 2)
    print signals
    if signals:
        for signal in signals:
            trade = Trader(signal, bot)
            trade.process()
            #q.put(signal)
        #q.join()
    print 'All jobs executed!'
    time.sleep(INTERVAL)
