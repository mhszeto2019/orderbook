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


class GetOrdersRequest(BaseModel):
   
 
   username:str
   redis_key:str
  
   

@app.post("/okxperp/get_all_open_orders")
async def get_all_open_orders(
   payload: GetOrdersRequest,
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
      exchange = ccxt.okx({
      'apiKey': api_creds_dict['okx_apikey'],
      'secret': api_creds_dict['okx_secretkey'],
      'password': api_creds_dict['okx_passphrase'],
      })


      # # markets = exchange.load_markets()
      open_orders = exchange.fetchOpenOrders()
      if len(open_orders) == 0:
         return []
      json_data = open_orders[0]
      
      json_response = {}
      json_response['exchange'] = 'okxperp'
      json_response['instrument_id'] = json_data['info']['instId']
      json_response['leverage'] = json_data['info']['lever']
      json_response['side'] = json_data['info']['side']
      json_response['offset'] = 'hedged'
      
      json_response['price'] = json_data['price']
      json_response['fill_size'] = json_data['info']['fillSz']
      json_response['order_type'] = json_data['info']['ordType']
      json_response['order_type_cancellation'] = ''

      json_response['order_id'] = json_data['info']['ordId']
      json_response['order_time'] = json_data['info']['uTime']
      json_response['amount'] = json_data['amount']

      json_response['ts'] = json_data['timestamp']
      json_response['attachAlgoOrds'] = json_data['info']['attachAlgoOrds']

      print(json_response)
      
      # [{'info': {'accFillSz': '0', 'algoClOrdId': '', 'algoId': '', 'attachAlgoClOrdId': '', 'attachAlgoOrds': [], 'avgPx': '', 'cTime': '1745572440071', 'cancelSource': '', 'cancelSourceReason': '', 'category': 'normal', 'ccy': '', 'clOrdId': '', 'fee': '0', 'feeCcy': 'BTC', 'fillPx': '', 'fillSz': '0', 'fillTime': '', 'instId': 'BTC-USD-SWAP', 'instType': 'SWAP', 'isTpLimit': 'false', 'lever': '5', 'linkedAlgoOrd': {'algoId': ''}, 'ordId': '2451823690830405632', 'ordType': 'limit', 'pnl': '0', 'posSide': 'net', 'px': '80000', 'pxType': '', 'pxUsd': '', 'pxVol': '', 'quickMgnType': '', 'rebate': '0', 'rebateCcy': 'BTC', 'reduceOnly': 'false', 'side': 'buy', 'slOrdPx': '', 'slTriggerPx': '', 'slTriggerPxType': '', 'source': '', 'state': 'live', 'stpId': '', 'stpMode': 'cancel_maker', 'sz': '1', 'tag': '', 'tdMode': 'cross', 'tgtCcy': '', 'tpOrdPx': '', 'tpTriggerPx': '', 'tpTriggerPxType': '', 'tradeId': '', 'uTime': '1745572440071'}, 'id': '2451823690830405632', 'clientOrderId': None, 'timestamp': 1745572440071, 'datetime': '2025-04-25T09:14:00.071Z', 'lastTradeTimestamp': None, 'lastUpdateTimestamp': 1745572440071, 'symbol': 'BTC/USD:BTC', 'type': 'limit', 'timeInForce': None, 'postOnly': None, 'side': 'buy', 'price': 80000.0, 'stopLossPrice': None, 'takeProfitPrice': None, 'triggerPrice': None, 'average': None, 'cost': 0.0, 'amount': 1.0, 'filled': 0.0, 'remaining': 1.0, 'status': 'open', 'fee': {'cost': 0.0, 'currency': 'BTC'}, 'trades': [], 'reduceOnly': False, 'fees': [{'cost': 0.0, 'currency': 'BTC'}], 'stopPrice': None}]


      return [json_response]

   except:
      logger.info(traceback.format_exc())
