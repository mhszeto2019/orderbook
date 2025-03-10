import okx.MarketData as MarketData

flag = "0"  # Production trading:0 , demo trading:1

marketDataAPI =  MarketData.MarketAPI(flag=flag)

from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS

import os
import json
import configparser
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)
app = Flask(__name__)

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','htx2')))

from util import token_required
from util import get_logger 
logger = get_logger(os.path.basename(__file__))


CORS(app)
config_source = 'htx_live_trade'
secretKey = config[config_source]['secretKey']
apiKey = config[config_source]['apiKey']

redis_host ='localhost'
redis_port = 6379
redis_db = 0  # Default database
import redis
r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
from htx2.HtxOrderClass import HuobiCoinFutureRestTradeAPI

import asyncio
import base64
from cryptography.fernet import Fernet
import requests

@app.route('/okx/gettradehistory', methods=['POST'])
def gettradehistory():
    data = request.get_json()
    ccy = data['ccy']
    # Retrieve the recent transactions of an instrument from the last 3 months with pagination
    result = marketDataAPI.get_history_trades(
        instId=ccy
    )
    # print(result)
    # print(result['data'])
    json_dict = {}
    json_dict['data']= result['data'][10::-1]
    json_dict['exchange'] = 'OKX'
    json_dict['ccy'] = ccy
    if 'SWAP' in ccy:
        json_dict['instrument'] = 'SWAP'
        json_dict['ccy'] = ccy.replace('-SWAP','')

    else:
        json_dict['instrument'] = "SPOT"
    for row in json_dict:
        print(row)
    print(json_dict)
    return json_dict

if __name__ == "__main__":
    app.run(port='5003')