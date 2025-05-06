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

# FastAPI app instance
app = FastAPI()
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


@app.get("/binanceperp/")
async def read_root():
    return {"message": "Welcome to the FastAPI with ccxt integration!"}


class FundingRateRequest(BaseModel):
    username: str
    redis_key: str
    ccy: str

# def normalize_contract_size(book_arr):
#     new_arr = []
#     divisor = 100
#     for px,sz,_ in book_arr:
#         new_arr.append([px,sz/divisor,_])
#     # print(new_arr)
#     return new_arr
 

@app.post("/binanceperp/get_last_trades")
async def get_last_trades(
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

        exchange = ccxtpro.binance({'newUpdates': False})
        # print(payload.ccy)
        ccy = payload.ccy
        # ccy = 'BTC-USD-SWAP'
        ccy_str = ccy.replace('-USD-SWAP','USD_PERP')
        if ccy_str:
            result = await exchange.fetch_trades(symbol=ccy_str)
            rows =  result[-10:]
           
            # print(rows)

            #    [{'id': '363916432', 'info': {'timestamp': '1745987111074', 'price': '94930.5', 'amount': '950.0', 'direction': 'buy', 'index_price': '94943.5', 'instrument_name': 'BTC-PERPETUAL', 'trade_seq': '247167115', 'mark_price': '94938.39', 'tick_direction': '1', 'contracts': '95.0', 'trade_id': '363916432'}, 'timestamp': 1745987111074, 'datetime': '2025-04-30T04:25:11.074Z', 'symbol': 'BTC/USD:BTC', 'order': None, 'type': None, 'side': 'buy', 'takerOrMaker': None, 'price': 94930.5, 'amount': 950.0, 'cost': 0.01000732114546958, 'fee': {'cost': None, 'currency': None}, 'fees': []}, {'id': '363916433', 'info': {'timestamp': '1745987111074', 'price': '94930.5', 'amount': '19930.0', 'direction': 'buy', 'index_price': '94943.5', 'instrument_name': 'BTC-PERPETUAL', 'trade_seq': '247167116', 'mark_price': '94938.39', 'tick_direction': '1', 'contracts': '1993.0', 'trade_id': '363916433'}, 'timestamp': 1745987111074, 'datetime': '2025-04-30T04:25:11.074Z', 'symbol': 'BTC/USD:BTC', 'order': None, 'type': None, 'side': 'buy', 'takerOrMaker': None, 'price': 94930.5, 'amount': 19930.0, 'cost': 0.20994306360969342, 'fee': {'cost': None, 'currency': None}, 'fees': []}, {'id': '363916434', 'info': {'timestamp': '1745987111077', 'price': '94930.5', 'amount': '12150.0', 'direction': 'buy', 'index_price': '94943.5', 'instrument_name': 'BTC-PERPETUAL', 'trade_seq': '247167117', 'mark_price': '94938.39', 'tick_direction': '1', 'contracts': '1215.0', 'trade_id': '363916434'}, 'timestamp': 1745987111077, 'datetime': '2025-04-30T04:25:11.077Z', 'symbol': 'BTC/USD:BTC', 'order': None, 'type': None, 'side': 'buy', 'takerOrMaker': None, 'price': 94930.5, 'amount': 12150.0, 'cost': 0.12798837043942674, 'fee': {'cost': None, 'currency': None}, 'fees': []}, {'id': '363916435', 'info': {'timestamp': '1745987111078', 'price': '94930.5', 'amount': '6810.0', 'direction': 'buy', 'index_price': '94943.5', 'instrument_name': 'BTC-PERPETUAL', 'trade_seq': '247167118', 'mark_price': '94938.39', 'tick_direction': '1', 'contracts': '681.0', 'trade_id': '363916435'}, 'timestamp': 1745987111078, 'datetime': '2025-04-30T04:25:11.078Z', 'symbol': 'BTC/USD:BTC', 'order': None, 'type': None, 'side': 'buy', 'takerOrMaker': None, 'price': 94930.5, 'amount': 6810.0, 'cost': 0.07173669157962931, 'fee': {'cost': None, 'currency': None}, 'fees': []}, {'id': '363916436', 'info': {'timestamp': '1745987111078', 'price': '94930.5', 'amount': '5110.0', 'direction': 'buy', 'index_price': '94943.5', 'instrument_name': 'BTC-PERPETUAL', 'trade_seq': '247167119', 'mark_price': '94938.39', 'tick_direction': '1', 'contracts': '511.0', 'trade_id': '363916436'}, 'timestamp': 1745987111078, 'datetime': '2025-04-30T04:25:11.078Z', 'symbol': 'BTC/USD:BTC', 'order': None, 'type': None, 'side': 'buy', 'takerOrMaker': None, 'price': 94930.5, 'amount': 5110.0, 'cost': 0.05382885374036795, 'fee': {'cost': None, 'currency': None}, 'fees': []}, {'id': '363916437', 'info': {'timestamp': '1745987111082', 'price': '94930.5', 'amount': '12120.0', 'direction': 'buy', 'index_price': '94943.5', 'instrument_name': 'BTC-PERPETUAL', 'trade_seq': '247167120', 'mark_price': '94938.39', 'tick_direction': '1', 'contracts': '1212.0', 'trade_id': '363916437'}, 'timestamp': 1745987111082, 'datetime': '2025-04-30T04:25:11.082Z', 'symbol': 'BTC/USD:BTC', 'order': None, 'type': None, 'side': 'buy', 'takerOrMaker': None, 'price': 94930.5, 'amount': 12120.0, 'cost': 0.12767234977167508, 'fee': {'cost': None, 'currency': None}, 'fees': []}, {'id': '363916438', 'info': {'timestamp': '1745987111084', 'price': '94930.5', 'amount': '11320.0', 'direction': 'buy', 'index_price': '94943.5', 'instrument_name': 'BTC-PERPETUAL', 'trade_seq': '247167121', 'mark_price': '94938.39', 'tick_direction': '1', 'contracts': '1132.0', 'trade_id': '363916438'}, 'timestamp': 1745987111084, 'datetime': '2025-04-30T04:25:11.084Z', 'symbol': 'BTC/USD:BTC', 'order': None, 'type': None, 'side': 'buy', 'takerOrMaker': None, 'price': 94930.5, 'amount': 11320.0, 'cost': 0.11924513196496384, 'fee': {'cost': None, 'currency': None}, 'fees': []}, {'id': '363916439', 'info': {'timestamp': '1745987111084', 'price': '94930.5', 'amount': '70.0', 'direction': 'buy', 'index_price': '94943.5', 'instrument_name': 'BTC-PERPETUAL', 'trade_seq': '247167122', 'mark_price': '94938.39', 'tick_direction': '1', 'contracts': '7.0', 'trade_id': '363916439'}, 'timestamp': 1745987111084, 'datetime': '2025-04-30T04:25:11.084Z', 'symbol': 'BTC/USD:BTC', 'order': None, 'type': None, 'side': 'buy', 'takerOrMaker': None, 'price': 94930.5, 'amount': 70.0, 'cost': 0.000737381558087232, 'fee': {'cost': None, 'currency': None}, 'fees': []}, {'id': '363916440', 'info': {'timestamp': '1745987111084', 'price': '94930.5', 'amount': '3260.0', 'direction': 'buy', 'index_price': '94943.5', 'instrument_name': 'BTC-PERPETUAL', 'trade_seq': '247167123', 'mark_price': '94938.39', 'tick_direction': '1', 'contracts': '326.0', 'trade_id': '363916440'}, 'timestamp': 1745987111084, 'datetime': '2025-04-30T04:25:11.084Z', 'symbol': 'BTC/USD:BTC', 'order': None, 'type': None, 'side': 'buy', 'takerOrMaker': None, 'price': 94930.5, 'amount': 3260.0, 'cost': 0.034340912562348246, 'fee': {'cost': None, 'currency': None}, 'fees': []}, {'id': '363916441', 'info': {'timestamp': '1745987111084', 'price': '94931.0', 'amount': '3410.0', 'direction': 'buy', 'index_price': '94943.5', 'instrument_name': 'BTC-PERPETUAL', 'trade_seq': '247167124', 'mark_price': '94938.39', 'tick_direction': '0', 'contracts': '341.0', 'trade_id': '363916441'}, 'timestamp': 1745987111084, 'datetime': '2025-04-30T04:25:11.084Z', 'symbol': 'BTC/USD:BTC', 'order': None, 'type': None, 'side': 'buy', 'takerOrMaker': None, 'price': 94931.0, 'amount': 3410.0, 'cost': 0.03592082670571257, 'fee': {'cost': None, 'currency': None}, 'fees': []}]
            
            json_dict['trades'] = rows
            # json_dict['ts'] = result['fundingTimestamp']
            json_dict['ccy'] = payload.ccy
            json_dict['exchange'] = 'binanceperp'
            logger.info(f"{payload.ccy}|{json_dict}")
            # print(result)
            # if result.get('data'):
            #     print('success')
            # result['ccy'] = funding_rate
            await exchange.close()

            return json_dict
        else:
            return {"error":"Empty symbol"}



    except Exception as e:
        print(f"Error in get_last_Trades: {e}")
        await exchange.close()
        return {"error":f"{e}"}

        # raise HTTPException(status_code=500, detail=str(e))
  

@app.on_event("shutdown")
async def shutdown_event():
    # Close the exchange connection when the app shuts down
    if exchange:
        await exchange.close()

