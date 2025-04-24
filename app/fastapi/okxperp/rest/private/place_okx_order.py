import json
import os
import configparser
# Define the config file path in a cleaner way

project_root = "/var/www/html"
print(project_root)
base_directory = os.path.abspath(os.path.join(project_root,'./orderbook'))  # 2 levels up from script
print(base_directory)
config_directory = os.path.join(base_directory, 'config_folder') 
print(config_directory)
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

# exchange = ccxt.huobi({
#    'apiKey': 'nbtycf4rw2-5475d1b1-fd22adf0-83746',
#    'secret': 'c5a5a686-b39d1d16-79864b22-f3e72',
#    'options': {
#        'defaultType': 'swap',
#    },
# })
exchange = ccxt.okx({
   'apiKey': 'a0de3940-5679-4939-957a-51c87a8502d9',
   'secret': 'FA44BCAAC3788C2AB4AFC77047930792',
   'password': 'falconstead@Trading2024',
})


markets = exchange.load_markets()


# exchange.verbose = True  # uncomment for debugging purposes if necessary


# # creating and canceling a linear swap (limit) order
# symbol = 'ADA/USDT:USDT'
# order_type = 'limit'
# side = 'buy'
# offset = 'open'
# leverage = 1
# amount = 1
# price = 1

# params = {'offset': offset, 'lever_rate': leverage}

# try:
#    # fetching current balance
#    balance = exchange.fetch_balance()
#    # print(balance)

#    # placing an order
#    order = exchange.create_order(symbol, order_type, side, amount, price, params)
#    # print(order)

#    # listing open orders
#    open_orders = exchange.fetch_open_orders(symbol)
#    # print(open_orders)

#    # canceling an order
#    cancelOrder = exchange.cancel_order(order['id'], symbol)
#    print(cancelOrder)
# except Exception as e:
#    print(type(e).__name__, str(e))


# creating and canceling inverse swap (limit) order

symbol = 'BTC-USD-SWAP'
order_type = 'limit'
side = 'buy'
offset = 'open'
leverage = 5
amount = 1
price = 80000

params = {'offset': offset, 'lever_rate': leverage}

try:
   # fetching current balance
   balance = exchange.fetch_positions(symbols=['BTC-USD-SWAP'])
   print(balance)
      # placing an order
   # order = exchange.create_order(symbol, order_type, side, amount, price, params)
   # print(order)

   # # listing open orders
   # open_orders = exchange.fetch_open_orders(symbol)
   # print(open_orders)

   # # canceling an order
   # cancelOrder = exchange.cancel_order(order['id'], symbol)

except Exception as e:
   print(type(e).__name__, str(e))
