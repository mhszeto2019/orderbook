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
  
   

@app.post("/deribitperp/get_all_positions")
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
    try:
        exchange = ccxt.deribit({
            'apiKey': api_creds_dict['deribit_apikey'],
            'secret': api_creds_dict['deribit_secretkey'],
        })
        # markets = exchange.load_markets()

        positions = exchange.fetch_positions(['BTC-PERPETUAL','ETH-PERPETUAL'])
        
        json_data = positions[0]
        logger.info(json_data)
        if not positions or positions[0]['info']['size']=='0.0':
            logger.info('no positions')
            return []
            
        logger.info(json_data)
        json_response = {}
        json_response['adl'] = ''
        json_response['exchange'] = 'deribitperp'
        json_response['instrument_id'] = json_data['info']['instrument_name'].replace('PERPETUAL','USD-SWAP')
        json_response['leverage'] = json_data['info']['leverage']
        json_response['margin_ratio'] = json_data['maintenanceMarginPercentage']
        json_response['position'] = float(json_data['info']['size'])/100 if json_data['info']['direction'] == 'buy' else -float(json_data['info']['size'])/100
        json_response['price'] = json_data['info']['average_price']
        json_response['pnl'] = json_data['info']['realized_profit_loss']
        json_response['liquidation_price'] = json_data['info']['estimated_liquidation_price']

        json_response['ts'] = json_data['timestamp']

     # [{'info': {'size': '10.0', 'kind': 'future', 'maintenance_margin': '1.057e-6', 'initial_margin': '2.113e-6', 'open_orders_margin': '7.781e-6', 'direction': 'buy', 'index_price': '94641.25', 'instrument_name': 'BTC-PERPETUAL', 'settlement_price': '94644.45', 'mark_price': '94642.17', 'interest_value': '-5.989412344071121e-6', 'delta': '1.05661e-4', 'average_price': '94640.0', 'leverage': '50', 'floating_profit_loss': '3.0e-9', 'realized_profit_loss': '0.0', 'total_profit_loss': '3.0e-9', 'realized_funding': '0.0', 'size_currency': '1.05661e-4', 'estimated_liquidation_price': '9135.11'}, 'id': None, 'symbol': 'BTC/USD:BTC', 'timestamp': 1746002391829, 'datetime': '2025-04-30T08:39:51.829Z', 'lastUpdateTimestamp': None, 'initialMargin': 2.113e-06, 'initialMarginPercentage': 1.9997917869412556, 'maintenanceMargin': 1.057e-06, 'maintenanceMarginPercentage': 1.000369104967774, 'entryPrice': 94640.0, 'notional': 0.000105661, 'leverage': 50, 'unrealizedPnl': 3e-09, 'contracts': None, 'contractSize': 10.0, 'marginRatio': None, 'liquidationPrice': 9135.11, 'markPrice': 94642.17, 'lastPrice': None, 'collateral': None, 'marginMode': None, 'side': 'long', 'percentage': None, 'hedged': None, 'stopLossPrice': None, 'takeProfitPrice': None}]

        print(json_response)
        logger.info(json_response)
        return [json_response]
    except Exception as e:
        print(e)
        logger.error(traceback.format_exc())
        return {"error":f"{e}"}




