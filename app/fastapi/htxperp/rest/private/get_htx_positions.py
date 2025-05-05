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
  
   

@app.post("/htxperp/get_all_positions")
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
        exchange = ccxt.huobi({
            'apiKey': api_creds_dict['htx_apikey'],
            'secret': api_creds_dict['htx_secretkey'],
            'options': {
                'defaultType': 'swap',
            },
        })

    # # markets = exchange.load_markets()
        # positions = exchange.fetch_positions(symbols=['BTC-USD'])
        positions = exchange.fetch_positions(symbols=['BTC-USD','ETH-USD'])
        logger.info(f"POSITIONS:{positions}")
        if not positions:
            logger.info('no positions')
            return []
        json_data = positions[0]
        logger.info(json_data)
        json_response = {}
        json_response['adl'] = json_data['info']['open_adl']
        json_response['exchange'] = 'htxperp'
        json_response['instrument_id'] = json_data['info']['contract_code'] + '-SWAP'
        json_response['leverage'] = json_data['info']['lever_rate']
        json_response['margin_ratio'] = json_data['info']['position_margin']
        json_response['position'] = json_data['info']['volume'] if json_data['side'] == 'long' else -float(json_data['info']['volume'])
        json_response['price'] = json_data['entryPrice']
        json_response['pnl'] = json_data['info']['profit_unreal']
        json_response['liquidation_price'] = json_data['info']['liq_px']

        json_response['ts'] = json_data['timestamp']


    # {'info': {'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': '2.000000000000000000', 'available': '2.000000000000000000', 'frozen': '0E-18', 'cost_open': '93681.595133096920507000', 'cost_hold': '93681.595133096920507000', 'profit_unreal': '0.000002274286583800000000000000000000000000000000000000', 'profit_rate': '0.005326469874286480', 'lever_rate': '5', 'position_margin': '0.000426523354819447', 'direction': 'buy', 'profit': '0.000002274286583800000000000000000000000000000000000000', 'liq_px': '63619.175984357167389881', 'last_price': '93781.5', 'store_time': '2025-04-25 15:28:20', 'open_adl': '1', 'adl_risk_percent': '2', 'tp_trigger_price': None, 'sl_trigger_price': None, 'tp_order_id': None, 'sl_order_id': None, 'tp_trigger_type': None, 'sl_trigger_type': None}, 'id': None, 'symbol': 'BTC/USD:BTC', 'contracts': 2.0, 'contractSize': 100.0, 'entryPrice': 93681.59513309693, 'collateral': None, 'side': 'long', 'unrealizedPnl': 2.2742865838e-06, 'leverage': 5.0, 'percentage': 0.532646987428648, 'marginMode': 'cross', 'notional': 0.002132616774097236, 'markPrice': None, 'lastPrice': None, 'liquidationPrice': None, 'initialMargin': 0.000426523354819447, 'initialMarginPercentage': 0.1999999999999999, 'maintenanceMargin': None, 'maintenanceMarginPercentage': None, 'marginRatio': None, 'timestamp': 1745568202981, 'datetime': '2025-04-25T08:03:22.981Z', 'hedged': None, 'lastUpdateTimestamp': None, 'stopLossPrice': None, 'takeProfitPrice': None}

        # [{'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1.0, 'available': 1.0, 'frozen': 0.0, 'cost_open': 95827.20000000004, 'cost_hold': 95827.20000000004, 'profit_unreal': 0.0, 'profit_rate': -1.845e-15, 'lever_rate': 5, 'position_margin': 0.000208709009550524, 'direction': 'buy', 'profit': 0.0, 'liq_px': 33313.866877150256, 'last_price': 95827.2, 'store_time': '2024-11-28 15:21:38', 'open_adl': 1, 'adl_risk_percent': 1, 'tp_trigger_price': None, 'sl_trigger_price': None, 'tp_order_id': None, 'sl_order_id': None, 'tp_trigger_type': None, 'sl_trigger_type': None}]
        logger.info(json_response)
        return [json_response]
    except Exception as e:
        logger.error(traceback.format_exc())
        return {"error":f"{e}"}




