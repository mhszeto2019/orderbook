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

# Assuming you're already running FastAPI
app = FastAPI()

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


config_source = 'deribit'
secretKey = config[config_source]['secretKey']
apiKey = config[config_source]['apiKey']




import ccxt 
exchange_deribit = ccxt.deribit({})

currencies_dict = {'deribit': {'futures': [], 'spot': []},
                    'okx': {'futures': [], 'spot': []},
                    'htx': {'futures': [], 'spot': []},
                    'binance': {'futures': [], 'spot': []}
                }   

for market_type in ['future', 'spot']:
    markets = exchange_deribit.fetch_markets({"kind": market_type})
    symbols = [m['symbol'] for m in markets]
    currencies_dict['deribit'][f'{market_type}s'] = symbols  # 'future' -> 'futures'


exchange_binancecoinm= ccxt.binancecoinm({})

for market_type in ['futures']:
    markets = exchange_binancecoinm.fetch_markets()
    symbols = [m['symbol'] for m in markets]
    currencies_dict['binance'][f'{market_type}'] = symbols  # 'future' -> 'futures'

exchange_binance= ccxt.binance({})

for market_type in ['spot']:
    markets = exchange_binance.fetch_markets()
    symbols = []
    for m in markets:
        if 'BTC/' in m['symbol']:
            symbols.append(m['symbol'])
        else:
            continue
    # symbols = [m['symbol'] if 'BTC' in m['symbol'] else continue for m in markets]
    currencies_dict['binance'][f'{market_type}'] = symbols  

exchange_htx= ccxt.htx({})

for market_type in ['spot']:
    markets = exchange_htx.fetch_markets({"symbol":"BTC"})
    symbols = []
    for m in markets:
        if 'BTC/' in m['symbol']:
            symbols.append(m['symbol'])
        else:
            continue
    # symbols = [m['symbol'] if 'BTC' in m['symbol'] else continue for m in markets]
    currencies_dict['htx'][f'{market_type}'] = symbols  


print(currencies_dict['htx'])
