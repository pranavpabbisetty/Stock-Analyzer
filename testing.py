import pandas as pd
from enum import Enum
import io
import requests

_EXCHANGE_LIST = ['nyse', 'nasdaq', 'amex']

headers = {
    'authority': 'api.nasdaq.com',
    'accept': 'application/json, text/plain, */*',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
    'origin': 'https://www.nasdaq.com',
    'sec-fetch-site': 'same-site',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://www.nasdaq.com/',
    'accept-language': 'en-US,en;q=0.9',
}


def params(exchange):
    return (
        ('letter', '0'),
        ('exchange', exchange),
        ('render', 'download'),
    )


params = (
    ('tableonly', 'true'),
    ('limit', '25'),
    ('offset', '0'),
    ('download', 'true'),
)


def params_region(region):
    return (
        ('letter', '0'),
        ('region', region),
        ('render', 'download'),
    )

def get_tickers_filtered(mktcap_min, mktcap_max):
    tickers_list = []
    for exchange in _EXCHANGE_LIST:
        tickers_list.extend(([mktcap_min, mktcap_max]))
    return tickers_list

if __name__ == '__main__':
    # get tickers filtered by market cap (in millions)
    filtered_tickers = get_tickers_filtered(mktcap_min=500, mktcap_max=2000)
    print(filtered_tickers[:10])