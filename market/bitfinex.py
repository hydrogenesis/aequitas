#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import traceback

from decimal import Decimal
import requests
import thread
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from datetime import timedelta, date
import json
from pytz import timezone
import base64
import hmac
import hashlib
import time
import StringIO
import csv
import types
from market import *
sys.path.append('../secret')
sys.path.append('../util')
from tlsadapter import *
from secret import *
from common import *
from multiprocessing import Process, Value, Lock

class Bitfinex(Market):
  def __init__(self, key, secret):
    Market.__init__(self, 'Bitfinex')
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    self.api = 'api.bitfinex.com/'
    self.interval = 2
    self.fiat = kUSD
    self.trade_fee = 0.002
    self.transaction_fee = 0.0
    self.min_lots = 0.01  # minimum lots
    self.max_lag = 20 # maximum lag of market
    self.key = key
    self.secret = secret
    self.nonce = long(time.time() * 100000)
    self.nonce_lock = Lock()

  def get_nonce(self):
    n = -1
    with self.nonce_lock:
      n = self.nonce
      self.nonce += 1
    return n

  def order_book(self, ticker="btcusd", bids=100, asks=100):
    path = "/v1/book/" + ticker + "?limit_bids=" + str(bids) + "&limit_asks=" + str(asks)
    payload = {}
    payload["request"] = path
    payload["limit_bids"] = str(bids)
    payload["limit_asks"] = str(asks)
    payload["nonce"] = str(self.get_nonce())
    headers = self._prepare_payload(True, payload)
    return self._get("https://" + self.api + path, headers=headers, verify=False)

  def balances(self):
    payload = {}
    payload["request"] = "/v1/balances"
    payload["nonce"] = str(self.get_nonce())
    headers = self._prepare_payload(True, payload)
    return self._get("https://" + self.api + "/v1/balances", headers=headers, verify=False)

  def lendbook(self, currency):
    return self._get("https://" + self.api + "/v1/lendbook/" + currency, verify=False)

  def offers(self):
    payload = {}
    payload["request"] = "/v1/offers"
    payload["nonce"] = str(self.get_nonce())
    headers = self._prepare_payload(True, payload)
    return self._get("https://" + self.api + "/v1/offers", headers=headers, verify=False)

  def cancel_offer(self, offer_id):
    payload = {}
    payload["request"] = "/v1/offer/cancel"
    payload["nonce"] = str(self.get_nonce())
    payload["offer_id"] = offer_id
    headers = self._prepare_payload(True, payload)
    return self._post("https://" + self.api + "/v1/offer/cancel", headers=headers, verify=False)

  def new_offer(self, amount, rate, period = 2, currency = 'USD', direction = 'lend'):
    payload = {}
    payload["request"] = "/v1/offer/new"
    payload["nonce"] = str(self.get_nonce())
    payload["currency"] = currency
    payload["amount"] = Truncate(amount, 6)
    payload["rate"] = '%.04f' %rate
    payload["period"] = period
    payload["direction"] = direction
    headers = self._prepare_payload(True, payload)
    print payload
    return self._post("https://" + self.api + "/v1/offer/new", headers=headers, verify=False)

  def credits(self):
    payload = {}
    payload["request"] = "/v1/credits"
    payload["nonce"] = str(self.get_nonce())
    headers = self._prepare_payload(True, payload)
    return self._get("https://" + self.api + "/v1/credits", headers=headers, verify=False)

  def interest_history(self, since_days, limit=1000):
    payload = {}
    payload["request"] = "/v1/history"
    payload["currency"] = "USD"
    d = datetime.datetime.now() + timedelta(days=since_days)
    payload["since"] = str(long((d - datetime.datetime(1970, 1, 1)).total_seconds()))
    payload["limit"] = limit
    payload["nonce"] = str(self.get_nonce())
    payload["wallet"] = "deposit"
    headers = self._prepare_payload(True, payload)
    print payload
    return self._post("https://" + self.api + "/v1/history", headers=headers, verify=False)

  def cryptowatch(self, api):
    return self._get('https://api.cryptowat.ch/' + api)
  def yunbi(self, symbol):
    return self._get('https://plugin.sosobtc.com/widgetembed/data/depth?symbol=yunbi' + symbol, proxies = localproxy)
  def poloniex(self, api):
    return self._get('https://poloniex.com/public?command=' + api)
    
  def _get(self, url, headers = None, verify = False, proxies = None):
    #s = requests.Session()
    #s.mount('https://', TlsAdapter())
    fail = True
    retry = 0
    while fail == True and retry <= kMaxRetries:
      try:
        retry += 1
	ret = requests.get(url, headers = headers, verify = verify, timeout = kTimeout, proxies = proxies)
        ret_json = ret.json()
        fail = False
      except:
        time.sleep(0.3)
        pass
    #print ret.text
    return ret.json()

  def _post(self, url, headers = None, verify = False):
    ret = requests.post(url, headers = headers, verify = verify, timeout = kTimeout)
    return ret.json()

  def _ticker(self, symbol="btcusd"):
    return self._get("https://" + self.api + "/v1/ticker/" + symbol, verify=False)

  def _ticker2(self, symbols=["tBTCUSD"]):
    url = "https://" + self.api + "/v2/tickers?symbols=" + ",".join(symbols)
    return self._get(url, verify=False)

  def _book(self, bids=10, asks=10, symbol="btcusd"):
    payload = {}
    payload['limit_bids'] = bids
    payload['limit_asks'] = asks
    headers = self._prepare_payload(False, payload)
    return self._get("https://" + self.api + "/v1/book/" + symbol, headers=headers, verify=False)

  def _prepare_payload(self, should_sign, d):
    j = json.dumps(d)
    data = base64.standard_b64encode(j)

    if should_sign:
      h = hmac.new(self.secret, data, hashlib.sha384)
      signature = h.hexdigest()
      return {
          "X-BFX-APIKEY": self.key,
          "X-BFX-SIGNATURE": signature,
          "X-BFX-PAYLOAD": data,
      }
    else:
      return {
          "X-BFX-PAYLOAD": data,
      }

if __name__ == "__main__":
  bitfinex = Bitfinex(bitfinex_key, bitfinex_secret)
  print json.dumps(bitfinex.balances(), indent=2)
