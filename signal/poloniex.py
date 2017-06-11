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

def GetTicker():
  url = 'https://poloniex.com/public?command=returnTicker'
  r = requests.get(url)
  return r.json()

def RetrieveChart(ticker, start, end, period):
  url = 'https://poloniex.com/public?command=returnChartData&currencyPair=%s&start=%d&end=%d&period=%d' %(ticker, start, end, period)
  print url
  r = requests.get(url)
  return r.json()

def UpdateData(period=86400*60, interval=12*3600):
  tickers = GetTicker()
  data = {}
  now = int(time.time())
  end = 9999999999
  begin = now - period
  for ticker in tickers:
    if not ticker.startswith('BTC_'): continue
    print 'getting', ticker
    data[ticker] = RetrieveChart(ticker, begin, end, interval)
  with open('poloniex.json', 'w') as f:
    f.write(json.dumps(data, indent=2))

if __name__ == '__main__':
  period = 86400*60
  interval=4*3600
  bar_num = period / interval
  UpdateData(period=period, interval=interval)
  slippery = 0.005
  with open('poloniex.json', 'r') as f:
    data = json.load(f)
  portfolio = {'BTC': 100.0}
  prices = []
  tickers = []
  for ticker in data:
    daily = []
    if len(data[ticker]) != bar_num:
      print ticker, len(data[ticker])
      continue
    days = 0
    for tick in data[ticker]:
      daily.append(tick['close'])
      if tick['volume'] < 10:
        days += 1
    #if days > 10:
    #  print ticker, days
    #  continue
    prices.append(daily)
    tickers.append(ticker)
  for day in range(1, len(prices[0])):
    #if day % 6 != 0: continue
    print 'bar', day, 
    delta_map = {}
    price_map = {}
    for i in range(len(tickers)):
      delta = (prices[i][day] / prices[i][day-1] - 1) * 100
      delta_map[tickers[i]] = delta
      price_map[tickers[i]] = prices[i][day]
    top10 = []
    last10 = []
    count = 0
    for key, value in sorted(delta_map.iteritems(), key=lambda (k,v): (v,k), reverse=True):
      if count < 10:
        top10.append([key, value])
      if count >= len(delta_map.keys()) - 10:
        last10.append([key, value])
      count += 1
    #print last10
    #print portfolio
    for asset in portfolio:
      if asset != 'BTC':
        portfolio['BTC'] += portfolio[asset]*price_map[asset] * (1-slippery)
        portfolio[asset] = 0.0
    #print portfolio
    # buy
    total = 0.0
    for asset in last10:
      total += asset[1]
    for asset in last10:
      weight = asset[1] / total
      money = portfolio['BTC'] * weight
      amount = money / price_map[asset[0]] * (1-slippery)
      portfolio[asset[0]] = amount
    portfolio['BTC'] = 0.0
    #print portfolio
    btc_value = 0
    for asset in portfolio:
      if asset != 'BTC':
        btc_value += portfolio[asset]*price_map[asset] *(1-slippery)
      else:
        btc_value += portfolio[asset]
    print btc_value
      




