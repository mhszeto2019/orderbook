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


class GetOrdersRequest(BaseModel):
   
 
   username:str
   redis_key:str
  
   

@app.post("/binanceperp/get_all_open_orders")
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

      exchange = ccxt.binancecoinm({
         'apiKey': api_creds_dict['binance_apikey'],
         'secret': api_creds_dict['binance_secretkey'],
         # 'verbose':True
      })
      exchange.options['portfolioMargin'] = True
      exchange.options["warnOnFetchOpenOrdersWithoutSymbol"] = False
      

      # # markets = exchange.load_markets()
      open_orders = exchange.fetchOpenOrders()

      if len(open_orders) == 0:
         return []
      json_data_arr = []
      for json_data in open_orders:
        
         json_response = {}
         json_response['exchange'] = 'binanceperp'
         json_response['instrument_id'] = json_data['info']['symbol'].replace('USD_PERP','-USD-SWAP')
         json_response['leverage'] = ''
         json_response['side'] = json_data['side']
         json_response['offset'] = ''
         json_response['price'] = json_data['price']
         json_response['fill_size'] = json_data['filled']
         # 1. Quotation; 2. Cancelled order; 3. Forced liquidation; 4. Delivery Order；22.ADL
         json_response['order_type'] = json_data['type'] 
         json_response['order_type_cancellation'] = json_data['info']['type'] 
         json_response['order_id'] = json_data['info']['orderId']
         json_response['order_time'] = json_data['info']['time']

         json_response['amount'] = json_data['amount']

         json_response['ts'] = json_data['timestamp']
         json_data_arr.append(json_response)

      print(json_data_arr)
      return json_data_arr

   except Exception as e:
      logger.info(traceback.format_exc())
      print(e)
      return  {"error":f"{e}"}

# [{'info': {'orderId': '173355713189', 'symbol': 'BTCUSD_PERP', 'pair': 'BTCUSD', 'status': 'NEW', 'clientOrderId': 'web_xktJGM2lqV2QEzOhTizP', 'price': '80000', 'avgPrice': '0', 'origQty': '1', 'executedQty': '0', 'cumBase': '0', 'timeInForce': 'GTC', 'type': 'LIMIT', 'reduceOnly': False, 'side': 'BUY', 'positionSide': 'BOTH', 'origType': 'LIMIT', 'time': '1746419158089', 'updateTime': '1746419158089', 'selfTradePreventionMode': 'EXPIRE_MAKER', 'priceMatch': 'NONE'}, 'id': '173355713189', 'clientOrderId': 'web_xktJGM2lqV2QEzOhTizP', 'timestamp': 1746419158089, 'datetime': '2025-05-05T04:25:58.089Z', 'lastTradeTimestamp': None, 'lastUpdateTimestamp': 1746419158089, 'symbol': 'BTC/USD:BTC', 'type': 'limit', 'timeInForce': 'GTC', 'postOnly': False, 'reduceOnly': False, 'side': 'buy', 'price': 80000.0, 'triggerPrice': None, 'amount': 1.0, 'cost': 0.0, 'average': None, 'filled': 0.0, 'remaining': 1.0, 'status': 'open', 'fee': None, 'trades': [], 'fees': [], 'stopPrice': None, 'takeProfitPrice': None, 'stopLossPrice': None}]


   return orders







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
