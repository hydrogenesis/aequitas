#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib
import urllib2
import hashlib
import simplejson
import sys
from market import *
sys.path.append('../..')
from secret import *

class OKCoin(Market):
  def __init__(self, partner, secret):
    Market.__init__(self, 'OKCoin')
    self.api = 'www.okcoin.cn/api/v1/'
    self.interval = 2
    self.fiat = kCNY
    self.trade_fee = 0.0
    self.transaction_fee = 0.0
    self.min_lots = 0.01  # minimum lots
    self.max_lag = 20 # maximum lag of market
    self.partner = partner
    self.secret = secret

  def update_book(self):
    Market.update_book(self)
    book = self._book("btc_cny")
    self.bids.clear()
    self.asks.clear()
    for ask in book['asks']:
      price = float(ask[0])
      if not price in self.asks:
        self.asks[price] = 0
      self.asks[price] += float(ask[1])
    for bid in book['bids']:
      price = float(bid[0])
      if not price in self.bids:
        self.bids[price] = 0
      self.bids[price] += float(bid[1])

  def get_info(self):
    params = {'partner' : self.partner}
    user_info_url = 'https://' + self.api + 'userinfo.do'
    return(self._post(params, user_info_url))

  def _get_json(self, url):
    response = urllib2.urlopen(url, timeout = kTimeout)
    data = simplejson.load(response)
    return(data)

  def _ticker(self, symbol="btc_cny"):
    r = self._get_json("https://" + self.api + "ticker.do?symbol=" + symbol)
    return r

  def _book(self, symbol="btcusd"):
    r = self._get_json("https://" + self.api + "depth.do?symbol=" + symbol)
    return r

  def _post(self, params, url):
    # params does not include the signed part, we add that
    sign_string = ''

    for pos,key in enumerate(sorted(params.keys())):
      sign_string += key + '=' + str(params[key])
      if( pos != len(params) - 1 ):
        sign_string += '&'

    sign_string += self.secret
    m = hashlib.md5()
    m.update(sign_string)
    signed = m.hexdigest().upper()

    params['sign'] = signed

    data = urllib.urlencode(params)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    result = simplejson.load(response)

    success = result[u'result']
    if( not success ):
      print('Error: ' + str(result[u'errorCode']))
      print( self.error_code_meaning(result[u'errorCode']) )
      return(result)
    else:
      return(result)


if __name__ == '__main__':
  okcoin = OKCoin(okcoin_partner, okcoin_secret)
  okcoin.update_status()
  print okcoin.unified_bids
  print okcoin.unified_asks
  print okcoin.best_bid
  print okcoin.best_ask
  print okcoin.get_info()
