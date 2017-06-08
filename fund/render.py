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
sys.path.append('../signal')
from common import *
from bitfinex import *
from market_data import *
from multiprocessing import Process, Value, Lock

def GenerateHTML(html):
  r = redis.StrictRedis(host='localhost', port=6379, db=0)
  md = MarketData()
  md.UpdateLedger()
  timestamp = GetTimestamp()
  redis_key = "LEDGER:%s:%s:%s" %("USD", "BITFINEX", 'DEPOSIT')
  ret = r.get(redis_key)
  print redis_key
  if ret == None: return False
  ledger = json.loads(ret)
  [ldate, lcurrency, lavailable, ltotal] = ledger
  print ledger
  redis_key_balance = 'BALANCE:%s:%s' %("USD", "BITFINEX")
  balance_sheet = json.loads(r.get(redis_key_balance))
  print json.dumps(balance_sheet)
  history_days = 100
  owners = []
  with open(html, 'w') as f:
    f.write("""<html><head>
        <title>Margin Funding Fund</title>
        <link rel="apple-touch-icon" href="/nemo.ico" />
        <meta charset="UTF-8">
        <style>
        tbody tr:nth-child(even)  td { background-color: #eee; }
        @media screen and (max-width: 1024px) {
          table {
            width: 96%;
            margin: 2%;
            overflow-x: auto;
            display: block;
          }
        }
        </style>
        </head><body>\n""")
    f.write('Date: %s\n'% datetime.datetime.fromtimestamp(int(ldate)/1000 + 8*3600).strftime('%Y/%m/%d %H:%M:%S'))
    f.write('<table border="1" cellpadding="0" cellspacing="0" style="font-size:20pt;min-width:900px;">\n')
    f.write("<tr><th>Owner</th><th>Position</th><th>Shares</th></tr>\n")
    balance_history = {}
    for owner in balance_sheet['shares']:
      owners.append(owner)
      share = Decimal(balance_sheet['shares'][owner]) / 100
      position = share * Decimal(ltotal)
      f.write("<tr><td>%s</td><td>$%.02f</td><td>%.04f%%</td></tr>\n" % (owner, position, share * 100))
      redis_key = "FUNDHISTORY:%s:%s:%s" %("USD", "BITFINEX", owner)
      history = r.lrange(redis_key, 0, history_days)
      print redis_key, history
      datavec = [timestamp, dec(position), ltotal]
      if history == None or len(history) <= 0:
        history = [json.dumps(datavec)]
        r.lpush(redis_key, json.dumps(datavec))
      else:
        last_day = json.loads(history[0])
        if last_day[2] != datavec[2]:  # total money increases
          r.lpush(redis_key, json.dumps(datavec))
        history = r.lrange(redis_key, 0, history_days)
      for day in history:
        day_data = json.loads(day)
        the_date = datetime.datetime.fromtimestamp(int(day_data[0])/1000 + 8*3600).strftime('%Y/%m/%d-%H:%M:%S')
        if not the_date in balance_history:
          balance_history[the_date] = {}
        balance_history[the_date][owner] = day_data
    print balance_history
    f.write("<tr><td>Total</td><td>$%.02f</td><td></td></tr>\n" % (Decimal(ltotal)))
    f.write('</table>\n')
    f.write('History\n<table border="1" cellpadding="0" cellspacing="0" style="font-size:20pt;min-width:900px;">\n')
    headers = "</th><th>".join(owners)
    f.write("<tr><th>Date</th><th>%s</th></tr>\n"%headers)
    for date in balance_history:
      data = []
      for owner in owners:
        if not owner in balance_history[date]:
          data.append("$0.00")
        else:
          data.append("$%.02f" %Decimal(balance_history[date][owner][1]))
      body = "</td><td>".join(data)
      f.write("<tr><td>%s</td><td>%s</td></tr>\n"%(date, body))
    f.write('</table>\n')
    f.write('</body></html>\n')

if __name__ == '__main__':
  GenerateHTML('fund.html')
