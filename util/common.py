#!/usr/bin/python
# -*- coding: utf-8 -*-

# constants
import time
from decimal import Decimal
kBTC = 0
kUSD = 10
kCNY = 20
kBTCDepth = 1  # Bitcoin depth to look for
# When the price difference is larger than kProfitEdge, it's a profitable circumstance
kProfitEdge = 0.005

kTimeout=30
kMaxRetries = 5
localproxy = {
    'http': 'socks5://localhost:7777',
    'https': 'socks5://localhost:7777'
}

kMaxTickers = 10000
kOrderBookBidDepth = 2
kOrderBookAskDepth = 2

CurrencySymbol = {
    'ZEC': u'\u24E9',
    'BTC': u'\u20BF',
    'ETH': u'\u039E',
    'USD': u'$'
}

def Truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d+'0'*n)[:n]])

def GetTimestamp():
  return str(int(time.time()*1000))

def dec(num):
  '''Convert num to decimal string'''
  return format(Decimal(num), '.8f')

def dec20(num):
  '''Convert num to decimal string'''
  return format(Decimal(num), '.20f')

if __name__ == "__main__":
  print Truncate(1.012456, 4)
  print "%.04f"%1.012456
  print GetTimestamp()
  print dec(0.1111111111)
  print dec20(0.1111111111)
