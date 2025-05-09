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

config_source = 'htx_live_trade'
htx_secretKey = config[config_source]['secretKey']
htx_apiKey = config[config_source]['apiKey']

config_source = 'okx'
okx_secretKey = config[config_source]['secretKey']
okx_apiKey = config[config_source]['apiKey']
okx_passphrase = config[config_source]['passphrase']

config_source = 'deribit'
deribit_secretKey = config[config_source]['secretKey']
deribit_apiKey = config[config_source]['apiKey']

config_source = 'binance'
binance_secretKey = config[config_source]['secretKey']
binance_apiKey = config[config_source]['apiKey']


exchange_huobi = ccxt.huobi({
            'apiKey': htx_apiKey,
            'secret': htx_secretKey,
            'options': {
                'defaultType': 'swap',
            },
        })

exchange_okx = ccxt.okx({
            'apiKey': okx_apiKey,
            'secret': okx_secretKey,
            'password':okx_passphrase
        })

exchange_deribit = ccxt.deribit({
            'apiKey':   deribit_apiKey,
            'secret':   deribit_secretKey,
        })

exchange_binance = ccxt.binancecoinm({
            'apiKey':   binance_apiKey,
            'secret':   binance_secretKey,
        })
exchange_binance.options['portfolioMargin'] = True


# HTX param str [params.type]: *inverse only* 'future', or 'swap'
# OKX param str [params.instType]: MARGIN, SWAP, FUTURES, OPTION
# DERIBIT param str [params.kind]: market type filter for positions 'future', 'option', 'spot', 'future_combo' or 'option_combo'

positions_htx =     exchange_huobi.fetchPositions(['BTC-USD','ETH-USD'],{'type':'swap'}) + exchange_huobi.fetchPositions(['BTC-USD','ETH-USD'],{'type':'future'})
positions_okx =     exchange_okx.fetchPositions([],{'instType':'SWAP'}) + exchange_okx.fetchPositions([],{'instType':'FUTURES'})
positions_deribit = exchange_deribit.fetchPositions([],{"currency":"BTC","kind":'future'}) 
positions_binance = exchange_binance.fetchPositions([]) 


# okx_liq_prices[contract_code] = {"liq_px":row['liqPx'],"last_px":row['last'],"direction":direction,"ts":current_ts.strftime('%Y-%m-%d %H:%M:%S')}

amount = {'deribit':0 ,'htx':0, "binance":0,'okx':0 ,'total':0}
for row in positions_deribit:
    print(row['info'])

    # print(row['info']['size'])
    amount['deribit'] += int(float(row['info']['size'])/100)
    amount['total'] += int(float(row['info']['size'])/100)

for row in positions_htx:
    print(row['info'])

    # print(row['info']['volume'])
    amount['htx'] += int(float(row['info']['volume'])) if row['info']['direction'] == 'buy' else  -int(float(row['info']['volume'])) 
    amount['total'] += int(float(row['info']['volume'])) if row['info']['direction'] == 'buy' else  -int(float(row['info']['volume'])) 

for row in positions_okx:
    print(row['info'])
    # print(row['info']['pos'])
    amount['okx'] += int(float(row['info']['pos']))
    amount['total'] += int(float(row['info']['pos']))


for row in positions_binance:
    # print(row['info']['positionAmt'])
    print(row['info'])
    amount['binance'] += int(float(row['info']['positionAmt']))
    amount['total'] += int(float(row['info']['positionAmt']))

print(amount)
 
# print(positions_deribit)

# deribit 'instrument_name': 'BTC-26SEP25'  'instrument_name': 'BTC-PERPETUAL'
# htx 'contract_code': 'BTC-USD',
# okx 'instId': 'BTC-USD-SWAP'
# binance 'symbol': 'BTCUSD_PERP'



# {'size': '-100.0', 'kind': 'future', 'maintenance_margin': '1.8847e-5', 'initial_margin': '3.7695e-5', 'open_orders_margin': '0.0', 'direction': 'sell', 'index_price': '103572.42', 'instrument_name': 'BTC-26SEP25', 'settlement_price': '106205.85', 'mark_price': '106115.91', 'delta': '-9.42366e-4', 'average_price': '105487.5', 'leverage': '25', 'floating_profit_loss': '7.98e-7', 'realized_profit_loss': '0.0', 'total_profit_loss': '-5.614e-6', 'size_currency': '-9.42366e-4', 'estimated_liquidation_price': '183492.29'}
# {'size': '-100.0', 'kind': 'future', 'maintenance_margin': '9.657e-6', 'initial_margin': '1.9314e-5', 'open_orders_margin': '0.0', 'direction': 'sell', 'index_price': '103572.42', 'instrument_name': 'BTC-PERPETUAL', 'settlement_price': '103660.08', 'mark_price': '103554.56', 'interest_value': '-8.506805109207218e-6', 'delta': '-9.65675e-4', 'average_price': '102438.16', 'leverage': '50', 'floating_profit_loss': '9.83e-7', 'realized_profit_loss': '0.0', 'total_profit_loss': '-1.0524e-5', 'realized_funding': '0.0', 'size_currency': '-9.65675e-4', 'estimated_liquidation_price': '179063.29'}
# {'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': '3.000000000000000000', 'available': '3.000000000000000000', 'frozen': '0E-18', 'cost_open': '102579.147939537966099142', 'cost_hold': '102579.147939537966099142', 'profit_unreal': '-0.000027070082163000000000000000000000000000000000000000', 'profit_rate': '-0.046280432715780945', 'lever_rate': '5', 'position_margin': '0.000579500181093806', 'direction': 'sell', 'profit': '-0.000027070082163000000000000000000000000000000000000000', 'liq_px': '140351.036539215735490784', 'last_price': '103537.5', 'store_time': '2025-05-09 11:22:34', 'open_adl': '1', 'adl_risk_percent': '5', 'tp_trigger_price': None, 'sl_trigger_price': None, 'tp_order_id': None, 'sl_order_id': None, 'tp_trigger_type': None, 'sl_trigger_type': None}
# {'adl': '1', 'availPos': '', 'avgPx': '102455.3932455492420727', 'baseBal': '', 'baseBorrowed': '', 'baseInterest': '', 'bePx': '101607.2200894913', 'bizRefId': '', 'bizRefType': '', 'cTime': '1746688608223', 'ccy': 'BTC', 'clSpotInUseAmt': '', 'closeOrderAlgo': [], 'deltaBS': '', 'deltaPA': '', 'fee': '-0.0000032466659157', 'fundingFee': '-0.0000005135929239', 'gammaBS': '', 'gammaPA': '', 'idxPx': '103577.6000000000000000', 'imr': '0.000579567352971', 'instId': 'BTC-USD-SWAP', 'instType': 'SWAP', 'interest': '', 'last': '103528.9', 'lever': '5', 'liab': '', 'liabCcy': '', 'liqPenalty': '0', 'liqPx': '68314.35634780499', 'margin': '', 'markPx': '103525.5', 'maxSpotInUseAmt': '', 'mgnMode': 'cross', 'mgnRatio': '121.3824443640013', 'mmr': '0.0000115913470594', 'nonSettleAvgPx': '', 'notionalUsd': '300', 'optVal': '', 'pendingCloseOrdLiabVal': '', 'pnl': '0.000029088565444', 'pos': '3', 'posCcy': '', 'posId': '2196480840296652800', 'posSide': 'net', 'quoteBal': '', 'quoteBorrowed': '', 'quoteInterest': '', 'realizedPnl': '0.0000253283066044', 'settledPnl': '', 'spotInUseAmt': '', 'spotInUseCcy': '', 'thetaBS': '', 'thetaPA': '', 'tradeId': '379237854', 'uTime': '1746777600334', 'upl': '0.0000302667785183', 'uplLastPx': '0.0000303619465825', 'uplRatio': '0.051683244922785', 'uplRatioLastPx': '0.0518457529467981', 'usdPx': '103577.6', 'vegaBS': '', 'vegaPA': ''}
# {'symbol': 'BTCUSD_PERP', 'positionAmt': '2', 'entryPrice': '102102.5827003', 'markPrice': '103532.1', 'unRealizedProfit': '0.00002705', 'liquidationPrice': '68470.62598971', 'leverage': '5', 'positionSide': 'BOTH', 'updateTime': '1746764417860', 'maxQty': '950', 'notionalValue': '0.00193177', 'breakEvenPrice': '96700.99335191'}