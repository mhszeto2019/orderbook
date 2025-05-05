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


class PositionRequest(BaseModel):
   
   username:str
   redis_key:str
  
   

@app.post("/binanceperp/get_all_positions")
async def get_all_positions(
    payload: PositionRequest,
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
    try:

        exchange = ccxt.binancecoinm({
            'apiKey': api_creds_dict['binance_apikey'],
            'secret': api_creds_dict['binance_secretkey'],
            # 'verbose':True
        })
        exchange.options['portfolioMargin'] = True
        
        print(exchange)
        # exchange.load_markets()
  
        positions = exchange.fetch_positions(['BTCUSD_PERP'])
        print(positions)
        if not positions:
            logger.info('no positions')
            return []
        json_data = positions[0]
        logger.info(json_data)
        json_response = {}
        json_response['adl'] = ''
        json_response['exchange'] = 'binanceperp'
        json_response['instrument_id'] = json_data['info']['symbol'].replace('USD_PERP','USD-SWAP')
        json_response['leverage'] = json_data['leverage']
        json_response['margin_ratio'] = json_data['maintenanceMarginPercentage']
        json_response['position'] = float(json_data['info']['positionAmt'])
        json_response['price'] = json_data['info']['entryPrice']
        json_response['pnl'] = json_data['info']['unRealizedProfit']
        json_response['liquidation_price'] = json_data['info']['liquidationPrice']
# 
        json_response['ts'] = json_data['timestamp']

# [{'info': {'symbol': 'BTCUSD_PERP', 'positionAmt': '2', 'entryPrice': '94105.34783971', 'markPrice': '94147.7', 'unRealizedProfit': '0.00000096', 'liquidationPrice': '64292.4579285', 'leverage': '5', 'positionSide': 'BOTH', 'updateTime': '1746416698478', 'maxQty': '950', 'notionalValue': '0.00212432', 'breakEvenPrice': '94138.28755126'}, 'id': None, 'symbol': 'BTC/USD:BTC', 'contracts': 2.0, 'contractSize': 100.0, 'unrealizedPnl': 9.6e-07, 'leverage': 5.0, 'liquidationPrice': 64292.4579285, 'collateral': 0.0, 'notional': 0.00212432, 'markPrice': 94147.7, 'entryPrice': 94105.34783971, 'timestamp': 1746416698478, 'initialMargin': 0.00042486, 'initialMarginPercentage': 0.2, 'maintenanceMargin': 8.49728e-06, 'maintenanceMarginPercentage': 0.004, 'marginRatio': None, 'datetime': '2025-05-05T03:44:58.478Z', 'marginMode': None, 'marginType': None, 'side': 'long', 'hedged': False, 'percentage': None, 'stopLossPrice': None, 'takeProfitPrice': None}]

    #     print(json_response)
    #     logger.info(json_response)
        return [json_response]
    except Exception as e:
        print(e)
        logger.error(traceback.format_exc())
        return {"error":f"{e}"}




