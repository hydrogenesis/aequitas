#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import traceback
import redis

from decimal import *
import requests
import thread
from datetime import timedelta, date, datetime
import json
from pytz import timezone
import base64
import hmac
import hashlib
import time
import StringIO
import csv
import types
sys.path.append('../util')
sys.path.append('../secret')
sys.path.append('../market')
from common import *
from bitfinex import *
from secret import *
from multiprocessing import Process, Value, Lock

class MarketData():
  def __init__(self):
    self.bitfinex = Bitfinex(bitfinex_key, bitfinex_secret)
    self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
    self.r.flushall()

  def UpdateAll(self):
    self.UpdateBitfinex()

  def UpdateBitfinex(self):
    balance = self.bitfinex.balances()
    # Update ledger
    date = GetTimestamp()
    ledger = {}
    for entry in balance:
      available = str(entry['available'])
      currency = str(entry['currency'].upper())
      total = str(entry['amount'])
      wallet = str(entry['type'].upper())
      if not currency in ledger: ledger[currency] = {}
      ledger[currency][wallet] = [date, currency, available, total]
    for ticker in ledger:
      for wallet in ledger[ticker]:
        redis_key = "LEDGER:%s:BITFINEX:%s" %(ticker, wallet)
        self.r.set(redis_key, json.dumps(ledger[ticker][wallet]))
        print redis_key, self.r.get(redis_key)
    # Update ticker
    query = ['BTCUSD', 'ETHUSD', 'ETHBTC', 'ETCUSD', 'ETCBTC', 'ZECUSD', 'ZECBTC', 'XMRUSD', 'XMRBTC', 'LTCUSD', 'LTCBTC', 'XRPUSD', 'XRPBTC', 'DASHUSD', 'DASHBTC']
    result_query = map(lambda x:'t'+x, query)
    date = GetTimestamp()
    bfx_ticker = self.bitfinex._ticker2(result_query)
    for entry in bfx_ticker:
      symbol, bid, bid_size, ask, ask_size, daily_change, dayly_change_percent, last, volume, high, low = entry
      symbol = symbol[1:]
      vector = [date, dec(last), dec(bid), dec(ask)]
      redis_key = "TICKER:%s:BITFINEX" % symbol
      current = self.r.lindex(redis_key, 0)
      if current != None:
        current = json.loads(current)
        if current[1] == vector[1] and current[2] == vector[2] and current[3] == vector[3]: continue
      self.r.lpush(redis_key, json.dumps(vector))
      if self.r.llen(redis_key) > kMaxTickers:
        self.r.rpop(redis_key)
     
      print redis_key, self.r.llen(redis_key)
      print redis_key, self.r.lrange(redis_key, 0, -1)

    # Update trading book
    for symbol in query:
      date = GetTimestamp()
      orders = self.bitfinex.order_book(symbol.lower(), kOrderBookBidDepth, kOrderBookAskDepth)
      if 'message' in orders: continue
      ask_book = []
      for ask in orders['asks']:
        vector = [str(int(float(ask['timestamp']))), dec(ask['price']), dec(ask['amount']), 1]
        ask_book.append(vector)
      bid_book = []
      for bid in orders['bids']:
        vector = [str(int(float(bid['timestamp']))), dec(bid['price']), dec(bid['amount']), 0]
        bid_book.append(vector)
      all_book = {'date': date, 'asks': ask_book, 'bids': bid_book}
      redis_key = "TRADINGBOOK:%s:BITFINEX" %symbol
      self.r.set(redis_key, json.dumps(all_book))
      print redis_key, json.loads(self.r.get(redis_key))['asks'][0], json.loads(self.r.get(redis_key))['bids'][0]

    # Update trading book
    currencies = ['USD', 'BTC', 'ETH', 'ZEC', 'ETC', 'XMR', 'LTC', 'DSH']
    for currency in currencies:
      date = GetTimestamp()
      orders = self.bitfinex.lendbook(currency)
      if 'message' in orders: continue
      ask_book = []
      for ask in orders['asks']:
        frr = ask['frr']
        is_frr = 0
        if frr == 'Yes': is_frr = 1
        vector = [str(int(float(ask['timestamp']))), dec(ask['rate']), dec(ask['amount']), str(ask['period']), 1, is_frr]
        ask_book.append(vector)
      bid_book = []
      for bid in orders['bids']:
        frr = bid['frr']
        is_frr = 0
        if frr == 'Yes': is_frr = 1
        vector = [str(int(float(bid['timestamp']))), dec(bid['rate']), dec(bid['amount']), str(bid['period']), 0, is_frr]
        bid_book.append(vector)
      all_book = {'date': date, 'asks': ask_book, 'bids': bid_book}
      redis_key = "FUNDINGBOOK:%s:BITFINEX" %currency
      self.r.set(redis_key, json.dumps(all_book))
      print redis_key, len(json.loads(self.r.get(redis_key))['asks']), len(json.loads(self.r.get(redis_key))['bids'])

if __name__ == '__main__':
  market_data = MarketData()
  market_data.UpdateAll()

