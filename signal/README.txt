# data formats

funding order: 
FUNDINGBOOK:SYMBOL:MARKET {date(timestamp), asks/bids:[{date(timestamp), interest(%.08f annual percentage), amount(%.08f), period(%d days), direction(0 demand|1 offer), flags}]}

trading order:
TRADINGBOOK:SYMBOL:MARKET {date(timestamp), asks/bids:[{date(timestamp), price(%.08f), amount(%.08f), direction(0 buy or bid|1 sell or ask)}]}

ledger entry:
LEDGER:SYMBOL:MARKET:WALLET  {date(timestamp), currency, available(%.08f), total(%.08f)}

market price:
TICKER:SYMBOL:MARKET [{date(timestamp), last(%.08f), bid(%.08f), ask(%.08f)}]

transactions:
TRANSACTION:SYMBOL:MARKET [{date(timestamp), amount(%.08f), direction(0 deposit|1 withdraw), balance(before transaction), owner, memo}]

balance sheet:
BALANCE:SYMBOL:MARKET {'date':date, 'total':total, 'shares':{'owner1':percentage1,...}}

balance sheet snapshot:
SNAPSHOT:SYMBOL:MARKET [{'date':date, 'balance':{}}]
