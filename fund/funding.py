#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import traceback

from decimal import Decimal
import requests
import thread
from datetime import timedelta, date, datetime
import json
import redis
from pytz import timezone
import base64
import hmac
import hashlib
import time
import StringIO
import csv
import types
sys.path.append('../util')
sys.path.append('../market')
from common import *
from bitfinex import *
from multiprocessing import Process, Value, Lock

def CreateFundingTx(market, currency, amount, is_deposit, owner, memo):
  tx_date = GetTimestamp()
  direction = 1 # 1 for withdraw, 0 for deposit
  r = redis.StrictRedis(host='localhost', port=6379, db=0)
  redis_key = "LEDGER:%s:%s:%s" %(currency, market, 'DEPOSIT')
  ret = r.get(redis_key)
  print redis_key
  if ret == None: return False
  ledger = json.loads(ret)
  [ldate, lcurrency, lavailable, ltotal] = ledger
  if is_deposit: direction = 0
  transaction = [tx_date, dec(amount), direction, ltotal, owner, memo]
  redis_key_balance = 'BALANCE:%s:%s' %(currency, market)
  old_sheet = r.get(redis_key_balance)
  print redis_key_balance, old_sheet
  new_sheet = CalculateBalaneSheet(transaction, old_sheet)
  trans_str = json.dumps(transaction)
  with open("ledger.txt", "a") as ledger_file:
    ledger_file.write(trans_str + "\n")
  redis_key = "TRANSACTION:%s:%s" %(currency, market)
  r.lpush(redis_key, trans_str)
  print r.lrange(redis_key, 0, -1)
  r.set(redis_key_balance, json.dumps(new_sheet))
  print redis_key_balance, r.get(redis_key_balance)

def CalculateBalaneSheet(transaction, balance_sheet = None):
  [tx_date, amount, direction, total, owner, memo] = transaction
  if balance_sheet == None:
    date = GetTimestamp()
    balance_sheet = {'date':date, 'total':"0.0", 'shares':{'omega':'100'}}
  else:
    print balance_sheet
    balance_sheet = json.loads(balance_sheet)
  original_balance = Decimal(0.0)
  original_total = Decimal(balance_sheet['total'])
  if owner in balance_sheet['shares']:
    original_balance = Decimal(balance_sheet['shares'][owner]) / 100 * original_total
  dec_amount = Decimal(amount)
  if direction == 1:  # withdraw
    if dec_amount > original_balance:
      print "Insufficient balance", dec_amount, original_balance
      return None
    new_balance = original_balance - dec_amount
    new_total = original_total - dec_amount
  else:
    new_balance = original_balance + dec_amount
    new_total = original_total + dec_amount
  new_sheet = {'date':GetTimestamp(), 'total':dec(new_total)}
  agent_balance = {}
  for agent in balance_sheet['shares']:
    agent_percentage = Decimal(balance_sheet['shares'][agent]) / 100
    agent_balance[agent] = agent_percentage * original_total
  agent_balance[owner] = new_balance
  agent_shares = {}
  for agent in agent_balance:
    percentage = agent_balance[agent] / new_total
    # use high precision for shares
    agent_shares[agent] = dec20(percentage * 100)
  new_sheet['shares'] = agent_shares
  return new_sheet

if __name__ == '__main__':
  CreateFundingTx('BITFINEX', 'USD', '162163.7', True, 'omega', 'test')
  CreateFundingTx('BITFINEX', 'USD', '184247.55', True, 'alpha', 'init')
  CreateFundingTx('BITFINEX', 'USD', '56372.0', True, 'beta', 'init')
