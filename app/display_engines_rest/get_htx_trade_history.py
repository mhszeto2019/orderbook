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

@app.route('/htx/gettradehistory', methods=['POST'])
async def gettradehistory():

    data = request.get_json()
    # username = data.get('username')
    # # Get the order data from the request
    # # okx_secretkey_apikey_passphrase = r.get('user:test123d:api_credentials"')
    # key_string = data.get('redis_key')
    # if key_string.startswith("b'") and key_string.endswith("'"):
    #     cleaned_key_string = key_string[2:-1]
    # else:
    #     cleaned_key_string = key_string  # Fallback if the format is unexpected

    # # Now decode the base64 string into bytes
    # key_bytes = base64.urlsafe_b64decode(cleaned_key_string)
    # key_bytes = cleaned_key_string.encode('utf-8')
    # # You can now use the key with Fernet
    # cipher_suite = Fernet(key_bytes)
    
    # cache_key = f"user:{username}:api_credentials"
    # # Fetch the encrypted credentials from Redis
    # encrypted_data = r.get(cache_key)   
    
    # if encrypted_data:
    # # Decrypt the credentials
    #     decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
    #     api_creds_dict = json.loads(decrypted_data)
        
    # Initialize TradeAPI
       
    try:
        # Data received from the client (assuming JSON body)
        instId = data.get('ccy','')
        
        instId= instId.replace("-SWAP", "")

        if not instId:
            return jsonify({"error": "instId is required"}), 400

        url = f"https://api.hbdm.com/swap-ex/market/trade?contract_code={instId}"

        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception if the HTTP request returned an unsuccessful status code
            data = response.json()
            data['exchange'] = 'htx'
            data['ccy'] =instId + '-SWAP'
            return jsonify(data)

        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500
    
    except Exception as e:
        print(e)

if __name__ == "__main__":
    app.run(port='6101')