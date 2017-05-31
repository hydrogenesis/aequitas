#!/usr/bin/python
# -*- coding: utf-8 -*-

import time, sys, datetime

sys.path.append('../util')
from common import *

class Market(object):
  '''Generalized market'''

  def __init__(self, name):
    self.name = name
    # market params
    self.api = ""  # api url
    self.interval = 2  # interval between API requests
    self.fiat = kCNY  # main fiat
    self.trade_fee = 0.0  # fee of trading
    self.transaction_fee = 0.0  # fee that happen at withdraw/deposit
    self.min_lots = 0.01  # minimum lots
    self.max_lag = 20 # maximum lag of market

    # will be updated in |update_status|
    self.bids = {}
    self.asks = {}
    self.unified_bids = []  # price in descending order
    self.unified_asks = []  # price in ascending order
    self.best_bid = -1.0
    self.best_ask = -1.0
    self.balance = {kBTC: 1.0, kCNY: 1000.0, kUSD: 100.0}
    self.last_check = 0
    self.success = False

  def can_buy(self, amount):
    ask = self.best_ask / (1 - self.trade_fee) / (1 - self.transaction_fee)
    return self.balance[self.fiat] > ask * amount

  def buy(self, amount):
    print "%s: buy %f at price %f" %(self.name, amount, self.best_ask)
    ask = self.best_ask / (1 - self.trade_fee) / (1 - self.transaction_fee)
    if self.can_buy(amount):
      print self.name, self.balance
      self.balance[kBTC] += amount
      self.balance[self.fiat] -= ask * amount
      print self.name, self.balance
    else: 
      print "%s: not enough fiat" %self.name

  def can_sell(self, amount):
    return self.balance[kBTC] > amount

  def sell(self, amount):
    print "%s: sell %f at price %f" %(self.name, amount, self.best_bid)
    bid = self.best_bid * (1 - self.trade_fee) * (1 - self.transaction_fee)
    if self.can_sell(amount):
      print self.name, self.balance
      self.balance[kBTC] -= amount
      self.balance[self.fiat] += bid * amount
      print self.name, self.balance
    else: 
      print "%s: not enough btc" %self.name

  def serialize(self):
    ts = datetime.datetime.fromtimestamp(self.last_check).strftime('%Y-%m-%d %H:%M:%S')
    return '[%s] %s: %.02f\t%.02f\t%s' %(ts, self.name, self.best_ask, self.best_bid, str(self.success))

  def lagged(self):
    return (time.time() - self.last_check) > self.max_lag

  def update_status(self):
    # print "%s: updating market status" %(self.name)
    try:
      self.update_book()
      self.sort_book()
      self.last_check = time.time()
      self.success = True
      # print "%s: market status update success" %(self.name)
    except Exception as e:
      self.success = False
      print e
      print "%s: market status update failed" %(self.name)
 
  def update_book(self):
    #print "%s: retrieving order book" %(self.name)
    return

  def sort_book(self):
    #print "%s: sorting order book to get a unified book" %(self.name)
    del self.unified_bids[:]
    del self.unified_asks[:]
    cum_ask = 0
    cum_bid = 0
    self.best_ask = -1
    self.best_bid = -1
    for price in sorted(self.asks, key = lambda key:key, reverse = False):
      if len(self.unified_asks) == 0 or self.unified_asks[-1][0] != price:
        self.unified_asks.append([price, self.asks[price]])
      else:
        self.unified_asks[-1][1] += self.asks[price]
      cum_ask += self.asks[price]
      if cum_ask > kBTCDepth and self.best_ask == -1:
        self.best_ask = price

    for price in sorted(self.bids, key = lambda key:key, reverse = True):
      if len(self.unified_bids) == 0 or self.unified_bids[-1][0] != price:
        self.unified_bids.append([price, self.bids[price]])
      else:
        self.unified_bidss[-1][1] += self.bids[price]
      cum_bid += self.bids[price]
      if cum_bid > kBTCDepth and self.best_bid == -1:
        self.best_bid = price

