import json
import os
import configparser
import traceback
# Define the config file path in a cleaner way

project_root = "/var/www/html"
base_directory = os.path.abspath(os.path.join(project_root,'./orderbook'))  # 2 levels up from script
config_directory = os.path.join(base_directory, 'config_folder') 
config_file_path = os.path.join(os.path.dirname(__file__), config_directory, 'credentials.ini')
# Ensure the config file exists before trying to load it
if not os.path.exists(config_file_path):
    raise FileNotFoundError(f"Config file not found at {config_file_path}")
# Initialize the config parser and read the file
config = configparser.ConfigParser()
config.read(config_file_path)

config_source = 'htx_live_trade'
secretKey = config[config_source]['secretKey']
apiKey = config[config_source]['apiKey']

from typing import Union
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import asyncio
import base64
from cryptography.fernet import Fernet


from app.util import token_required,get_logger

# Set up basic logging configuration
logger = get_logger()

redis_host ='localhost'
redis_port = 6379
redis_db = 0  # Default database

# import okx.PublicData as PublicData
# API initialization

from cryptography.fernet import Fernet
import base64


from fastapi import FastAPI, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import base64
import json
from cryptography.fernet import Fernet
import redis
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from typing import Optional


# Redis setup (update with your actual config)
r = redis.Redis(host='localhost', port=6379, db=0)

from fastapi import Depends

import ccxt.pro as ccxtpro
import ccxt  # noqa: E402

import asyncio
from typing import Dict


from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import base64, json
from cryptography.fernet import Fernet


# Define the Redis connection
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

print('CCXT Version:', ccxt.__version__)

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


import ccxt 
import re
exchange_deribit = ccxt.deribit({})
exchange_binancecoinm= ccxt.binancecoinm({})
exchange_binance= ccxt.binance({})
exchange_htx= ccxt.htx({})
exchange_okx= ccxt.okx({})


currencies_dict = {'deribit': {'futures': ['--Not Selected--'], 'spot': ['--Not Selected--']},
                    'okx': {'futures': ['--Not Selected--'], 'spot': ['--Not Selected--']},
                    'htx': {'futures': ['--Not Selected--'], 'spot': ['--Not Selected--']},
                    'binance': {'futures': ['--Not Selected--'], 'spot': ['--Not Selected--']}
                }   
# DERIBIT
deriibit_fut = exchange_deribit.fetch_markets({"kind": 'future'})
symbols = [m['symbol'] for m in deriibit_fut]
btc_usd_futures= [item for item in symbols if item.startswith('BTC/USD')]
currencies_dict['deribit']['futures']+=sorted(btc_usd_futures )

deribit_spot = exchange_deribit.fetch_markets({"kind": 'spot'})
symbols = [m['symbol'] for m in deribit_spot]
btc_usd_spot =  [item for item in symbols if item.startswith('BTC')]
currencies_dict['deribit']['spot']+=(btc_usd_spot   )
print(currencies_dict['deribit']['spot'])

# OKX 
okx_fut = exchange_okx.fetch_markets()
symbols = [m['symbol'] for m in okx_fut]
btc_usd_futures= [item for item in symbols if item.startswith('BTC/USD')]
btc_usd_spot = [item for item in btc_usd_futures if not (item.endswith('-C') or item.endswith('-P') or  ':' in item)]
btc_usd_futures = [item for item in btc_usd_futures if not (item.endswith('-C') or item.endswith('-P')) and ':' in item]
currencies_dict['okx']['spot'] +=btc_usd_spot 
currencies_dict['okx']['futures']+=sorted(btc_usd_futures)

# HTX 
htx_fut = exchange_htx.fetch_markets()
symbols = [m['symbol'] for m in htx_fut]
btc_usd_futures= [item for item in symbols if item.startswith('BTC/USD')]
btc_usd_spot = [item for item in btc_usd_futures if not (item.endswith('-C') or item.endswith('-P') or  ':' in item)]
btc_usd_futures = [item for item in btc_usd_futures if not (item.endswith('-C') or item.endswith('-P') ) and ':' in item]
currencies_dict['htx']['spot'] +=sorted(btc_usd_spot )
currencies_dict['htx']['futures']+=sorted(btc_usd_futures )
print(currencies_dict['htx']['futures'])
# print(currencies_dict['deribit']['spot'])
# print(currencies_dict['deribit']['futures'])
# print(currencies_dict['okx']['futures'])

# binance
binance_fut = exchange_binance.fetch_markets()
symbols = [m['symbol'] for m in binance_fut]
btc_usd_futures= [item for item in symbols if item.startswith('BTC/USD')]
btc_usd_spot = [item for item in btc_usd_futures if not (item.endswith('-C') or item.endswith('-P') or  ':' in item)]
btc_usd_futures = [item for item in btc_usd_futures if not (item.endswith('-C') or item.endswith('-P')) and ':' in item]
currencies_dict['binance']['spot']+=sorted(btc_usd_spot )
currencies_dict['binance']['futures']+=sorted(btc_usd_futures )

# print(currencies_dict['binance']['spot'])
# print(currencies_dict['binance']['futures'])


@app.get("/deribitperp/get_currencies_for_funding_rate")
async def get_currencies_for_funding_rate():
        
    # currencies_dict = {'deribit': {'futures': ['--Not Selected--'], 'spot': ['--Not Selected--']},
    #                     'okx': {'futures': ['--Not Selected--'], 'spot': ['--Not Selected--']},
    #                     'htx': {'futures': ['--Not Selected--'], 'spot': ['--Not Selected--']},
    #                     'binance': {'futures': ['--Not Selected--'], 'spot': ['--Not Selected--']}
    #                 }   
    # # DERIBIT
    # deriibit_fut = exchange_deribit.fetch_markets({"kind": 'future'})
    # symbols = [m['symbol'] for m in deriibit_fut]
    # btc_usd_futures= [item for item in symbols if item.startswith('BTC/USD')]
    # currencies_dict['deribit']['futures']+=sorted(btc_usd_futures )

    # deribit_spot = exchange_deribit.fetch_markets({"kind": 'spot'})
    # symbols = [m['symbol'] for m in deribit_spot]
    # btc_usd_spot =  [item for item in symbols if item.startswith('BTC')]
    # currencies_dict['deribit']['spot']+=(btc_usd_spot   )
    # print(currencies_dict['deribit']['spot'])

    # # OKX 
    # okx_fut = exchange_okx.fetch_markets()
    # symbols = [m['symbol'] for m in okx_fut]
    # btc_usd_futures= [item for item in symbols if item.startswith('BTC/USD')]
    # btc_usd_spot = [item for item in btc_usd_futures if not (item.endswith('-C') or item.endswith('-P') or  ':' in item)]
    # btc_usd_futures = [item for item in btc_usd_futures if not (item.endswith('-C') or item.endswith('-P')) and ':' in item]
    # currencies_dict['okx']['spot'] +=btc_usd_spot 
    # currencies_dict['okx']['futures']+=sorted(btc_usd_futures)

    # # HTX 
    # htx_fut = exchange_htx.fetch_markets()
    # symbols = [m['symbol'] for m in htx_fut]
    # btc_usd_futures= [item for item in symbols if item.startswith('BTC/USD')]
    # btc_usd_spot = [item for item in btc_usd_futures if not (item.endswith('-C') or item.endswith('-P') or  ':' in item)]
    # btc_usd_futures = [item for item in btc_usd_futures if not (item.endswith('-C') or item.endswith('-P') ) and ':' in item]
    # currencies_dict['htx']['spot'] +=sorted(btc_usd_spot )
    # currencies_dict['htx']['futures']+=sorted(btc_usd_futures )
    # print(currencies_dict['htx']['futures'])
    # # print(currencies_dict['deribit']['spot'])
    # # print(currencies_dict['deribit']['futures'])
    # # print(currencies_dict['okx']['futures'])

    # # binance
    # binance_fut = exchange_binance.fetch_markets()
    # symbols = [m['symbol'] for m in binance_fut]
    # btc_usd_futures= [item for item in symbols if item.startswith('BTC/USD')]
    # btc_usd_spot = [item for item in btc_usd_futures if not (item.endswith('-C') or item.endswith('-P') or  ':' in item)]
    # btc_usd_futures = [item for item in btc_usd_futures if not (item.endswith('-C') or item.endswith('-P')) and ':' in item]
    # currencies_dict['binance']['spot']+=sorted(btc_usd_spot )
    # currencies_dict['binance']['futures']+=sorted(btc_usd_futures )

    # # print(currencies_dict['binance']['spot'])
    # # print(currencies_dict['binance']['futures'])

    return currencies_dict

if __name__ == "__main__":
    asyncio.run(get_currencies_for_funding_rate())