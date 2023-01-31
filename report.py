import ccxt
import configparser
from tabulate import tabulate
import pandas as pd

config = configparser.ConfigParser()
config.optionxform = str
config.read('exchanges.config')

exhange_configs = [e for e in config if e != 'DEFAULT']

for exchange_id in exhange_configs:
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class(dict(config[exchange_id].items())) # passes all config key-value pairs to the class constructor

    data = None

    if exchange.has["fetchPositions"]:
        data = exchange.fetch_positions(params={'consolidation': 'market'})

# {'pair': 'XETHZUSD', 'positions': '16', 'type': 'buy', 'leverage': '3.93117', 'cost': '146492.29987', 'fee': '110.07242', 'vol': '105.65780641', 'vol_closed': '5.65780641', 'margin': '35462.36312'}        
        
print(data)
