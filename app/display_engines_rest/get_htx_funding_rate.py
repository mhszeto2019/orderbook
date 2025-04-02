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
logger = logging.getLogger('htx_funding_rate')
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

@token_required
@app.route('/htx/getfundingrate', methods=['POST'])
async def getfundingrate():
    print('getting htx_funding_rate')
    try:

        data = request.get_json()
        username = data.get('username')
        # Get the order data from the request
        # okx_secretkey_apikey_passphrase = r.get('user:test123d:api_credentials"')
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
            
            # Data received from the client (assuming JSON body)
            instId = data.get('ccy','')
            
            contract_code= instId.replace("-SWAP", "")
            tdMode= "cross"
        
            tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
            fundingrate = await tradeApi.get_funding_rate(contract_code,body = {
                "contract_code": contract_code
                }
                )

            position_data = fundingrate.get('data', [])
            position_data['ts'] = fundingrate['ts']
            position_data['ccy']= instId
            return position_data
        
    except Exception as e:
        logger.debug(e)
        return "TOKEN ERROR"

    return "TOKEN ERROR"

if __name__ == "__main__":
    app.run(port='5002')