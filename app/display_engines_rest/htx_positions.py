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
# Logger 
# Define the log directory and the log file name
from pathlib import Path
LOG_DIR = Path('/var/www/html/orderbook/logs')
log_filename = LOG_DIR / (Path(__file__).stem + '.log')
import os
os.makedirs(LOG_DIR, exist_ok=True)
# Set up basic logging configuration
import logging
file_handler = logging.FileHandler(log_filename)
# Set up a basic formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger = logging.getLogger('htx_positions')
logger.setLevel(logging.INFO)  # Set log level
# Add the file handler to the logger
logger.addHandler(file_handler)



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
# Initialize the Trade API client
# tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",secretKey,apiKey)

# get_open_orders means opening an order


@token_required
@app.route('/htx/get_all_positions', methods=['POST'])
async def get_all_htx_positions():
    data = request.get_json()
    
    username = data.get('username')
    # Get the order data from the request
    key_string = data.get('redis_key')
    if key_string.startswith("b'") and key_string.endswith("'"):
        cleaned_key_string = key_string[2:-1]
    else:
        cleaned_key_string = key_string  # Fallback if the format is unexpected

    # Now decode the base64 string into bytes
    key_bytes = base64.urlsafe_b64decode(cleaned_key_string)
    key_bytes = cleaned_key_string.encode('utf-8')
    # You can now use the key with Fernet
    cipher_suite = Fernet(key_bytes)
    
    cache_key = f"user:{username}:api_credentials"
    # Fetch the encrypted credentials from Redis
    encrypted_data = r.get(cache_key)   
    
    if encrypted_data:
    # Decrypt the credentials
        decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
        api_creds_dict = json.loads(decrypted_data)
        
    # Initialize TradeAPI
       
    try:
        # Data received from the client (assuming JSON body)
        instId = data.get('instId','')
        
        # instId= data["instId"].replace("-SWAP", "")

        tdMode= "cross"
       
        # Extract necessary parameters from the request
        # print(data)
      
       

        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_apikey'],api_creds_dict['htx_secretkey'])

        positions = await tradeApi.get_positions(instId,body = {
            "contract_code": instId
            }
            )
        position_data = positions.get('data', []) if positions else []
        # [{'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1.0, 'available': 1.0, 'frozen': 0.0, 'cost_open': 95827.20000000004, 'cost_hold': 95827.20000000004, 'profit_unreal': 0.0, 'profit_rate': -1.845e-15, 'lever_rate': 5, 'position_margin': 0.000208709009550524, 'direction': 'buy', 'profit': 0.0, 'liq_px': 33313.866877150256, 'last_price': 95827.2, 'store_time': '2024-11-28 15:21:38', 'open_adl': 1, 'adl_risk_percent': 1, 'tp_trigger_price': None, 'sl_trigger_price': None, 'tp_order_id': None, 'sl_order_id': None, 'tp_trigger_type': None, 'sl_trigger_type': None}]
        return position_data
    
    except Exception as e:
        print(e)

if __name__ == "__main__":
    app.run(port='5071')