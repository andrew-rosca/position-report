import configparser
import socket
from pprint import pprint

import ccxt
import pandas as pd
import requests
from requests_toolbelt.adapters import source
from tabulate import tabulate


def fetch_exchange_data(exchange_id):
    exchange_class = getattr(ccxt, exchange_id)
    class_params = dict(config[exchange_id].items())

    if exchange_id in ['binance', 'binanceus']: #Binance rejects requests via IPv6; need to override and pass a custom HTTP Session object
        class_params['session'] = get_ipv4_session()

    exchange = exchange_class(class_params) # passes all config key-value pairs to the class constructor

    exchange_dict = {}

    exchange_dict['balances'] = exchange.fetch_balance()

    if exchange_id not in ['binanceus']: #ccxt fails when requesting positions for Binance.US
        position_data = exchange.fetch_positions(params={'consolidation': 'market'})
        
        if exchange_id == 'kraken':
            position_data = parse_kraken_positions(position_data) #ccxt doesn't fully implement the Kraken API, so we need to parse the response manually

        exchange_dict['positions'] = position_data

    return exchange_dict

def parse_kraken_positions(position_data):
    # {'pair': 'XETHZUSD', 'positions': '16', 'type': 'buy', 'leverage': '3.93117', 'cost': '146492.29987', 'fee': '110.07242', 'vol': '105.65780641', 'vol_closed': '5.65780641', 'margin': '35462.36312'}        
    #TODO: implement this
    return position_data

def consolidate_positions(data):
    #position_data = pd.DataFrame(columns=['pair', 'exchange','value', 'source'])
    position_data = []
        
    for exchange_id in data:
        if 'balances' in data[exchange_id]:
            balances = data[exchange_id]['balances']['total']
            for currency in balances:
                value = balances[currency]
                if value != 0:
                    position_data.append({'pair': currency, 'exchange': exchange_id, 'value': value, 'source': 'balances'})

        #TODO: implement this
        if 'positions' in data[exchange_id]:
            positions = data[exchange_id]['positions']
            for item in positions:
                value = float(item['vol'])
                currency = item['pair']
                if value != 0:
                    position_data.append({'pair': currency, 'exchange': exchange_id, 'value': value, 'source': 'positions'})

    return position_data

def print_position_report(exchange_configs):
    data = {}

    for exchange_id in exhange_configs:
        data[exchange_id] = fetch_exchange_data(exchange_id)
        
    positions = consolidate_positions(data)

    print_summary(positions)

def print_summary(positions):
    df = pd.DataFrame(positions).query('value > 1') #somewhat arbitrary filter for very small values
    df = df.groupby(['pair']).sum().reset_index()

    df['value'] = df['value'].apply(lambda x: '{:.2f}'.format(x))

    print(tabulate(df, headers='keys', tablefmt='psql'))

def get_ipv4_session():
    local_ipv4 = socket.gethostbyname(socket.gethostname())
    src = source.SourceAddressAdapter(local_ipv4)

    session = requests.Session()
    session.mount("https://", src)

    return session

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read('exchanges.config')

    exhange_configs = [e for e in config if e != 'DEFAULT']

    print_position_report(exhange_configs)