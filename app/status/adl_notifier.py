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

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]
# FastAPI app instance
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config_source = 'htx_live_trade'
htx_secretKey = config[config_source]['secretKey']
htx_apiKey = config[config_source]['apiKey']

config_source = 'okx'
okx_secretKey = config[config_source]['secretKey']
okx_apiKey = config[config_source]['apiKey']
okx_passphrase = config[config_source]['passphrase']

config_source = 'deribit'
deribit_secretKey = config[config_source]['secretKey']
deribit_apiKey = config[config_source]['apiKey']

config_source = 'binance'
binance_secretKey = config[config_source]['secretKey']
binance_apiKey = config[config_source]['apiKey']


exchange_huobi = ccxt.huobi({
            'apiKey': htx_apiKey,
            'secret': htx_secretKey,
            'options': {
                'defaultType': 'swap',
            },
        })

exchange_okx = ccxt.okx({
            'apiKey': okx_apiKey,
            'secret': okx_secretKey,
            'password':okx_passphrase
        })

exchange_deribit = ccxt.deribit({
            'apiKey':   deribit_apiKey,
            'secret':   deribit_secretKey,
        })

exchange_binance = ccxt.binance({
            'apiKey':   binance_apiKey,
            'secret':   binance_secretKey,
        })

for ccy in ['BTC-USD','ETH-USD']:
    # HTX param str [params.type]: *inverse only* 'future', or 'swap'
    balance_htx = exchange_huobi.fetchPositions([ccy],{'type':'swap'})
    # OKX param str [params.instType]: MARGIN, SWAP, FUTURES, OPTION
    balance_okx = exchange_huobi.fetchPositions([ccy],{'instType':'SWAP'})
    # DERIBIT param str [params.kind]: market type filter for positions 'future', 'option', 'spot', 'future_combo' or 'option_combo'
    balance_deribit = exchange_deribit.fetchPositions([],{"currency":"BTC","kind":'future'})

    print(balance_deribit)