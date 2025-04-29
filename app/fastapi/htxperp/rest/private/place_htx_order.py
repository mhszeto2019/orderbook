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

# FastAPI app instance
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
   

@app.post("/htxperp/place_order")
async def place_order(
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
   try:
      exchange = ccxt.huobi({
         'apiKey': api_creds_dict['htx_apikey'],
         'secret': api_creds_dict['htx_secretkey'],
         'options': {
            'defaultType': 'swap',
         },
      })

      symbol = payload.instrument.replace('-SWAP','')
      order_type = payload.ordType
      
      amount=payload.sz
      side = payload.side
      price = payload.px
      # order_type = 'limit'
      # price = '80000'
      params = {'offset': payload.offset, 'lever_rate': 5}

      if order_type == 'counterparty1':
      
         order_type = 'opponent'


      elif order_type == 'counterparty5':
      
         order_type = 'optimal_5'

      elif order_type == 'queue1':
         print('queu1')
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

      elif order_type == 'market':
         order_type = 'optimal_20'

      order = exchange.create_order(symbol, order_type, side, amount, price, params)
      # {'info': {'order_id': '1365014534415097856', 'order_id_str': '1365014534415097856'}, 'id': '1365014534415097856', 'clientOrderId': None, 'timestamp': None, 'datetime': None, 'lastTradeTimestamp': None, 'symbol': 'BTC/USD:BTC', 'type': None, 'timeInForce': None, 'postOnly': None, 'side': None, 'price': None, 'triggerPrice': None, 'average': None, 'cost': None, 'amount': None, 'filled': None, 'remaining': None, 'status': None, 'reduceOnly': None, 'fee': None, 'trades': [], 'fees': [], 'lastUpdateTimestamp': None, 'stopPrice': None, 'takeProfitPrice': None, 'stopLossPrice': None}
      return order

   except Exception as e:
      logger.error(traceback.format_exc())

      # huobi {"status":"error","err_code":1047,"err_msg":"Insufficient margin available.","ts":1745917192657}

# okx {"code":"1","data":[{"clOrdId":"e847386590ce4dBCcc699096ccdc169c","ordId":"","sCode":"51008","sMsg":"Order failed. Insufficient BTC margin in account ","tag":"e847386590ce4dBC","ts":"1745917206076"}],"inTime":"1745917206076432","msg":"All operations failed","outTime":"1745917206077022"}
      return {'error':f'{e}'}





class CancelByIdTradeRequest(BaseModel):
   username:str
   redis_key:str
   order_id:str
   instrument_id:str
 

@app.post("/htxperp/cancel_order_by_id")
async def cancel_order_by_id(
   payload: CancelByIdTradeRequest,
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
 
   exchange = ccxt.huobi({
      'apiKey': api_creds_dict['htx_apikey'],
      'secret': api_creds_dict['htx_secretkey'],
      'options': {
         'defaultType': 'swap',
      },
   })

   print(payload.order_id)
   instrument_id = payload.instrument_id
   if "SWAP" in instrument_id:
      instrument_id = instrument_id.replace('-SWAP','')
   canceled_order = exchange.cancelOrder(payload.order_id,instrument_id)

   return canceled_order



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
