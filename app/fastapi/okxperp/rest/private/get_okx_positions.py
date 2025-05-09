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


class PositionRequest(BaseModel):
   
   username:str
   redis_key:str
  
   

@app.post("/okxperp/get_all_positions")
async def get_all_positions(
    payload: PositionRequest,
    token_ok: bool = Depends(token_required)  # your FastAPI-compatible token checker
    ):
    json_dict = {}

    key_string = payload.redis_key
    exchange = await get_exchange(payload.username,key_string)



    try:
        

        # # markets = exchange.load_markets()
        # positions = exchange.fetch_positions(symbols=['BTC-USD-SWAP'])
        # positions = exchange.fetch_positions()
        positions1 = exchange.fetchPositions([],{'instType':'SWAP'})
        positions2 = exchange.fetchPositions([],{'instType':'FUTURES'})

        positions = positions1 + positions2

        if not positions:
            logger.info('no positions')
            return []

      
        
        logger.info(f"POSITIONS:{positions}")
        if not positions:
            logger.info('no positions')
            return []

        json_data_arr = []
        for json_data in positions :

            json_response = {}
            json_response['adl'] = json_data['info']['adl']
            json_response['exchange'] = 'okxperp'
            json_response['instrument_id'] = json_data['info']['instId']
            json_response['leverage'] = json_data['info']['lever']
            json_response['margin_ratio'] = json_data['info']['mgnRatio']
            json_response['position'] = json_data['info']['pos']
            json_response['price'] = json_data['info']['avgPx']
            json_response['pnl'] = json_data['info']['pnl']
            json_response['liquidation_price'] = json_data['info']['liqPx']

            json_response['ts'] = json_data['info']['uTime']
            json_data_arr.append(json_response)

        return json_data_arr

    except:
        logger.info(traceback.format_exc())




# from ccxt
# [{'info': {'adl': '1', 'availPos': '', 'avgPx': '93569.9', 'baseBal': '', 'baseBorrowed': '', 'baseInterest': '', 'bePx': '93523.12674331748', 'bizRefId': '', 'bizRefType': '', 'cTime': '1745566099680', 'ccy': 'BTC', 'clSpotInUseAmt': '', 'closeOrderAlgo': [], 'deltaBS': '', 'deltaPA': '', 'fee': '-0.0000002671799371', 'fundingFee': '0', 'gammaBS': '', 'gammaPA': '', 'idxPx': '93664.9000000000000000', 'imr': '0.0002135583954076', 'instId': 'BTC-USD-SWAP', 'instType': 'SWAP', 'interest': '', 'last': '93650', 'lever': '5', 'liab': '', 'liabCcy': '', 'liqPenalty': '0', 'liqPx': '', 'margin': '', 'markPx': '93651.2', 'maxSpotInUseAmt': '', 'mgnMode': 'cross', 'mgnRatio': '312.70652070310155', 'mmr': '0.0000042711679082', 'nonSettleAvgPx': '', 'notionalUsd': '100', 'optVal': '', 'pendingCloseOrdLiabVal': '', 'pnl': '0', 'pos': '-1', 'posCcy': '', 'posId': '2196480840296652800', 'posSide': 'net', 'quoteBal': '', 'quoteBorrowed': '', 'quoteInterest': '', 'realizedPnl': '-0.0000002671799371', 'settledPnl': '', 'spotInUseAmt': '', 'spotInUseCcy': '', 'thetaBS': '', 'thetaPA': '', 'tradeId': '376843597', 'uTime': '1745566099680', 'upl': '-0.0000009277715134', 'uplLastPx': '-0.0000009140891816', 'uplRatio': '-0.0043405743866604', 'uplRatioLastPx': '-0.0042765616657769', 'usdPx': '93664.9', 'vegaBS': '', 'vegaPA': ''}, 'id': '2196480840296652800', 'symbol': 'BTC/USD:BTC', 'notional': 0.001067791977038201, 'marginMode': 'cross', 'liquidationPrice': None, 'entryPrice': 93569.9, 'unrealizedPnl': -9.277715134e-07, 'realizedPnl': -2.671799371e-07, 'percentage': -0.43405743866604, 'contracts': 1.0, 'contractSize': 100.0, 'markPrice': 93651.2, 'lastPrice': None, 'side': 'short', 'hedged': False, 'timestamp': 1745566099680, 'datetime': '2025-04-25T07:28:19.680Z', 'lastUpdateTimestamp': 1745566099680, 'maintenanceMargin': 4.2711679082e-06, 'maintenanceMarginPercentage': 0.004, 'collateral': 0.0002126306238942, 'initialMargin': 0.0002135583954076, 'initialMarginPercentage': 0.1999, 'leverage': 5.0, 'marginRatio': 0.02, 'stopLossPrice': None, 'takeProfitPrice': None}]   

# from okx
# {'code': '0', 'data': [{'adl': '1', 'availPos': '', 'avgPx': '93511.7', 'baseBal': '', 'baseBorrowed': '', 'baseInterest': '', 'bePx': '93567.82385715279', 'bizRefId': '', 'bizRefType': '', 'cTime': '1732693584348', 'ccy': 'BTC', 'clSpotInUseAmt': '', 'closeOrderAlgo': [], 'deltaBS': '', 'deltaPA': '', 'fee': '-0.0000003208154701', 'fundingFee': '0', 'gammaBS': '', 'gammaPA': '', 'idxPx': '93470.8000000000000000', 'imr': '', 'instId': 'BTC-USD-SWAP', 'instType': 'SWAP', 'interest': '', 'last': '93523.8', 'lever': '5', 'liab': '', 'liabCcy': '', 'liqPenalty': '0', 'liqPx': '78261.60025833434', 'margin': '0.0002138769800998', 'markPx': '93516.3', 'maxSpotInUseAmt': '', 'mgnMode': 'isolated', 'mgnRatio': '46.525355824765654', 'mmr': '0.0000042773291929', 'notionalUsd': '100', 'optVal': '', 'pendingCloseOrdLiabVal': '', 'pnl': '0', 'pos': '1', 'posCcy': '', 'posId': '2019681002234920961', 'posSide': 'net', 'quoteBal': '', 'quoteBorrowed': '', 'quoteInterest': '', 'realizedPnl': '-0.0000003208154701', 'spotInUseAmt': '', 'spotInUseCcy': '', 'thetaBS': '', 'thetaPA': '', 'tradeId': '332996199', 'uTime': '1732693584348', 'upl': '0.0000000526022794', 'uplLastPx': '0.0000001383557693', 'uplRatio': '0.0002459464285909', 'uplRatioLastPx': '0.0006468941595617', 'usdPx': '', 'vegaBS': '', 'vegaPA': ''}], 'msg': ''}




