import json
import os
import configparser
import traceback
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

app = FastAPI()

# Redis setup (update with your actual config)
r = redis.Redis(host='localhost', port=6379, db=0)

from fastapi import Depends

import ccxt.pro as ccxtpro
import asyncio
from typing import Dict


from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import base64, json
from cryptography.fernet import Fernet


# Define the Redis connection
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Define the request model using Pydantic for type validation
class FundingRateRequest(BaseModel):
    username: str
    redis_key: str  # The Redis key containing the encrypted API credentials
    ccy: str        # Currency pair (for example, 'BTC-USDT')

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Initialize FastAPI app

# Define a global exchange object to be used across multiple requests if needed
exchange = None




@app.get("/deribitperp/")
async def read_root():
    return {"message": "Welcome to the FastAPI with ccxt integration!"}


class FundingRateRequest(BaseModel):
    username: str
    redis_key: str
    ccy: str

@app.post("/deribitperp/funding_rate")
async def get_funding_rate(
    payload: FundingRateRequest,
    token_ok: bool = Depends(token_required)  # your FastAPI-compatible token checker
):
    json_dict = {}
    try:
        # Clean the base64-encoded redis_key
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

        exchange = ccxtpro.deribit({'newUpdates': False})
        ccy = payload.ccy

        
        result = await exchange.fetchFundingRate(payload.ccy)
        # print(result)
        # {'info': {'jsonrpc': '2.0', 'result': '6.126574098570054e-7', 'usIn': '1745982573767768', 'usOut': '1745982573770051', 'usDiff': '2283', 'testnet': False}, 'symbol': 'BTC/USD:BTC', 'markPrice': None, 'indexPrice': None, 'interestRate': None, 'estimatedSettlePrice': None, 'timestamp': None, 'datetime': None, 'fundingRate': 6.126574098570054e-07, 'fundingTimestamp': None, 'fundingDatetime': None, 'nextFundingRate': None, 'nextFundingTimestamp': None, 'nextFundingDatetime': None, 'previousFundingRate': None, 'previousFundingTimestamp': None, 'previousFundingDatetime': None, 'interval': '8h'}


        json_dict['funding_rate'] =result['fundingRate']
        json_dict['ts'] = 'NA'
        json_dict['ccy'] = payload.ccy
        json_dict['exchange'] = 'deribitperp'

        logger.info(f"{payload.ccy}|{json_dict}")
        await exchange.close()
        # print(result)
        # if result.get('data'):
        #     print('success')
        # result['ccy'] = funding_rate
        return json_dict

    except Exception as e:
        print(f"Error in get_funding_rate: {e}")
        logger.error(traceback.format_exc())
        await exchange.close()

        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    # Close the exchange connection when the app shuts down
    if exchange:
        await exchange.close()

