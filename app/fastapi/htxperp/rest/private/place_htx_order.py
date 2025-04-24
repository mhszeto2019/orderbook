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

exchange = ccxt.huobi({
   'apiKey': 'nbtycf4rw2-5475d1b1-fd22adf0-83746',
   'secret': 'c5a5a686-b39d1d16-79864b22-f3e72',
   'options': {
       'defaultType': 'swap',
   },
})
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
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class TradeRequest(BaseModel):
   
   leadingExchange:str
   laggingExchange:str
   instrument1:str
   instrument2:str
   ordType:str
   px1:str
   px2:str
   sz:int
   side:str
   username:str
   redis_key:str

@app.post("/htxperp/place_market_order")
async def place_market_order(
   payload: TradeRequest,
   token_ok: bool = Depends(token_required)  # your FastAPI-compatible token checker
):
   json_dict = {}

   key_string = payload.redis_key
   if key_string.startswith("b'") and key_string.endswith("'"):
      cleaned_key_string = key_string[2:-1]
   else:
      cleaned_key_string = key_string

   # Decode and prepare the key
   key_bytes = base64.urlsafe_b64decode(cleaned_key_string)
   key_bytes = cleaned_key_string.encode('utf-8')
   cipher_suite = Fernet(key_bytes)

   # Fetch encrypted credentials from Redis
   cache_key = f"user:{payload.username}:api_credentials"
   encrypted_data = r.get(cache_key)

   
   if not encrypted_data:
      raise HTTPException(status_code=404, detail="Credentials not found")

   # Decrypt the credentials
   decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
   api_creds_dict = json.loads(decrypted_data)
   print(api_creds_dict)

   exchange = ccxt.huobi({
      'apiKey': api_creds_dict['htx_apikey'],
      'secret': api_creds_dict['htx_secretkey'],
      'options': {
         'defaultType': 'swap',
      },
   })

   markets = exchange.load_markets()
   balance = exchange.fetch_positions(symbols=['BTC-USD'])
   print(payload)
   # order = exchange.create_order(symbol, order_type, side, amount, price, params)

   print(balance)



# symbol = 'BTC-USD'
# order_type = 'limit'
# side = 'buy'
# offset = 'open'
# leverage = 5
# amount = 1
# price = 80000

# params = {'offset': offset, 'lever_rate': leverage}

# try:
#    # fetching current balance
   
#    # balance = exchange.fetch_positions(symbols=['BTC-USD'])
#    # print(balance)
#    for i in range(5):
#          # placing an order
#       order = exchange.create_order(symbol, order_type, side, amount, price, params)
#       print(order)

#    # # listing open orders
#    # open_orders = exchange.fetch_open_orders(symbol)
#    # print(open_orders)

#       # canceling an order
#       cancelOrder = exchange.cancel_order(order['id'], symbol)
#       print(cancelOrder)

# except Exception as e:
#    print(type(e).__name__, str(e))
