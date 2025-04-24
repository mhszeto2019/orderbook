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

# # Define a function to fetch the order book continuously using ccxt.pro
# async def fetch_funding_rate():
#     global exchange
#     exchange = ccxtpro.okx({'newUpdates': False})
#     while True:
#         try:
#             # Watch the order book of 'BTC/USD'
#             funding_rate = await exchange.fetch_funding_rate('BTC-USD-SWAP')
#             # print("Ask:", funding_rate['asks'][0], "Bid:", funding_rate['bids'][0])
#             print(funding_rate)
#         except Exception as e:
#             print(f"Error in fetching funding_rate: {e}")
#             break


@app.get("/okxperp/")
async def read_root():
    return {"message": "Welcome to the FastAPI with ccxt integration!"}


class FundingRateRequest(BaseModel):
    username: str
    redis_key: str
    ccy: str

@app.post("/okxperp/funding_rate")
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

        exchange = ccxtpro.okx({'newUpdates': False})
        print(payload.ccy)
        result = await exchange.fetch_funding_rate(payload.ccy)
        print(result)
        # {'info': {'formulaType': 'noRate', 'fundingRate': '0.0001033844565710', 'fundingTime': '1745222400000', 'impactValue': '', 'instId': 'BTC-USD-SWAP', 'instType': 'SWAP', 'interestRate': '', 'maxFundingRate': '0.00375', 'method': 'current_period', 'minFundingRate': '-0.00375', 'nextFundingRate': '', 'nextFundingTime': '1745251200000', 'premium': '0.0002413359809591', 'settFundingRate': '0.0000278737528630', 'settState': 'settled', 'ts': '1745210420272'}, 'symbol': 'BTC/USD:BTC', 'markPrice': None, 'indexPrice': None, 'interestRate': 0.0, 'estimatedSettlePrice': None, 'timestamp': None, 'datetime': None, 'fundingRate': 0.000103384456571, 'fundingTimestamp': 1745222400000, 'fundingDatetime': '2025-04-21T08:00:00.000Z', 'nextFundingRate': None, 'nextFundingTimestamp': 1745251200000, 'nextFundingDatetime': '2025-04-21T16:00:00.000Z', 'previousFundingRate': None, 'previousFundingTimestamp': None, 'previousFundingDatetime': None, 'interval': None}
        json_dict['funding_rate'] =result['info']['fundingRate']
        json_dict['ts'] = result['fundingTimestamp']
        json_dict['ccy'] = payload.ccy
        json_dict['exchange'] = 'okxperp'

        logger.info(f"{payload.ccy}|{json_dict}")
        await exchange.close()
        # print(result)
        # if result.get('data'):
        #     print('success')
        # result['ccy'] = funding_rate
        return json_dict

    except Exception as e:
        print(f"Error in get_funding_rate: {e}")
        await exchange.close()

        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    # Close the exchange connection when the app shuts down
    if exchange:
        await exchange.close()

