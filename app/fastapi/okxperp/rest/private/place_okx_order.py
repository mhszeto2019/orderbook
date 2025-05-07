
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

# exchange = ccxt.huobi({
#    'apiKey': 'nbtycf4rw2-5475d1b1-fd22adf0-83746',
#    'secret': 'c5a5a686-b39d1d16-79864b22-f3e72',
#    'options': {
#        'defaultType': 'swap',
#    },
# })
# exchange = ccxt.okx({
#    'apiKey': 'a0de3940-5679-4939-957a-51c87a8502d9',
#    'secret': 'FA44BCAAC3788C2AB4AFC77047930792',
#    'password': 'falconstead@Trading2024',
# })

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

from okx import Trade,SpreadTrading

class TradeRequest(BaseModel):
   
   leadingExchange:str
   laggingExchange:str
   instrument1:str
   instrument2:str
   instrument:str
   ordType:str
   px1:str
   px2:str
   px:str
   sz:int
   side:str
   username:str
   redis_key:str
   offset:str
   offset1:str
   offset2:str

# exchange = ccxt.okx({
#    'apiKey': 'a0de3940-5679-4939-957a-51c87a8502d9',
#    'secret': 'FA44BCAAC3788C2AB4AFC77047930792',
#    'password': 'falconstead@Trading2024',
#    })
# exchange.load_markets()

exchange_pool = {}
pool_lock = asyncio.Lock()

async def get_exchange(username: str,key_string) -> ccxt.okx:
    async with pool_lock:
         if username in exchange_pool:
            return exchange_pool[username]
        
         if key_string.startswith("b'") and key_string.endswith("'"):
             cleaned_key_string = key_string[2:-1]
         else:
            cleaned_key_string = key_string

         # Decode and prepare the key
         key_bytes = base64.urlsafe_b64decode(cleaned_key_string)
         key_bytes = cleaned_key_string.encode('utf-8')
         cipher_suite = Fernet(key_bytes)

         # Fetch encrypted credentials from Redis
         cache_key = f"user:{username}:api_credentials"
         encrypted_data = r.get(cache_key)

         
         if not encrypted_data:
            raise HTTPException(status_code=404, detail="Credentials not found")

         # Decrypt the credentials
         decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
         api_creds_dict = json.loads(decrypted_data)

         # Initialize ccxt.okx and store in the pool
         exchange = ccxt.okx({
            'apiKey': api_creds_dict['okx_apikey'],
            'secret': api_creds_dict['okx_secretkey'],
            'password': api_creds_dict['okx_passphrase'],
            'enableRateLimit': True
         })

         exchange_pool[username] = exchange
         return exchange


from fastapi.exceptions import RequestValidationError
import time
@app.post("/okxperp/place_order")
@app.exception_handler(RequestValidationError)
async def place_order(
   payload: TradeRequest,
   token_ok: bool = Depends(token_required)  # your FastAPI-compatible token checker
):
   current_ts = time.time()
   json_dict = {}

   key_string = payload.redis_key
   exchange = await get_exchange(payload.username,key_string)
  
   try:
   
      symbol = payload.instrument
      order_type = payload.ordType
      side = payload.side
      amount=payload.sz
      price = payload.px
      params = {'offset': payload.offset, 'lever_rate': 5}

      if order_type == 'counterparty1':
         
         ticker = exchange.fetchTicker(symbol)
         bid = ticker['bid']
         # bid_sz = ticker['bidVolume']
         ask = ticker['ask']
         # ask_sz = ticker['askVolume']
         order_type = 'limit'

         # if buy , we buy ask price
         if side == 'buy': 
            price = ask
         else:
            price = bid
      elif order_type == 'counterparty5':
         ticker = exchange.fetchOrderBook(symbol,5)
         bid = ticker['bids'][0][0]
         # bid_sz = ticker['bidVolume']
         ask = ticker['asks'][0][0]
         # ask_sz = ticker['askVolume']
         order_type = 'limit'

         # if buy , we buy ask price
         if side == 'buy': 
            price = ask
         else:
            price = bid
            
      elif order_type == 'queue1':
         ticker = exchange.fetchTicker(symbol)
         bid = ticker['bid']
         # bid_sz = ticker['bidVolume']
         ask = ticker['ask']
         # ask_sz = ticker['askVolume']
         order_type = 'post_only'

         # if buy , we buy ask price
         if side == 'buy': 
            price = bid
         else:
            price = ask



      order = exchange.create_order(symbol, order_type, side, amount, price, params)
      logger.info(f"[{payload.username}]{order}")
      logger.info(time.time() - current_ts)
      return order
   except Exception as e:
      logger.error(traceback.format_exc())
      
      return {'error':f'{e}'}


class CancelByIdTradeRequest(BaseModel):
   username:str
   redis_key:str
   order_id:str
   instrument_id:str
 

@app.post("/okxperp/cancel_order_by_id")
async def cancel_order_by_id(
   payload: CancelByIdTradeRequest,
   token_ok: bool = Depends(token_required)  # your FastAPI-compatible token checker
):
   json_dict = {}

   key_string = payload.redis_key
   exchange = await get_exchange(payload.username,key_string)

   
   canceled_order = exchange.cancelOrder(payload.order_id,payload.instrument_id)
   logger.info(f"[{payload.username}]{canceled_order}")

   return canceled_order

   


