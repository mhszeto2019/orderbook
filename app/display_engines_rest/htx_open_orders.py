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
import os
from pathlib import Path
# Define the log directory and the log file name
LOG_DIR = Path('/var/www/html/orderbook/logs')
log_filename = LOG_DIR / (Path(__file__).stem + '.log')
os.makedirs(LOG_DIR, exist_ok=True)
# Set up basic logging configuration
import logging
file_handler = logging.FileHandler(log_filename)
# Set up a basic formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger = logging.getLogger('htx_open_orders')
logger.setLevel(logging.DEBUG)  # Set log level
# Add the file handler to the logger
logger.addHandler(file_handler)

CORS(app)

redis_host ='localhost'
redis_port = 6379
redis_db = 0  # Default database
import redis
r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
from htx2.HtxOrderClass import HuobiCoinFutureRestTradeAPI
import datetime
from datetime import datetime

import asyncio
import base64
from cryptography.fernet import Fernet
# Initialize the Trade API client
# tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",secretKey,apiKey)

@token_required
@app.route('/htx/swap/get_order_info', methods=['POST'])
async def get_order_info():
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
        instId= instId.replace("-SWAP", "")
        tdMode= "cross"
        # Extract necessary parameters from the request
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_apikey'],api_creds_dict['htx_secretkey'])
        print('data',data)
        order_infos = await tradeApi.get_order_info(instId,
            body = {
            "order_id":data['ordId'],
            "contract_code": instId
            }
        )
        order_info = order_infos.get('data', [])
        
        return order_info
    
    except Exception as e:
        logger.error(e)

@token_required
@app.route('/htx/swap/get_tpsl_info', methods=['POST'])
async def get_tpsl_info():
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
        instId= instId.replace("-SWAP", "")
        tdMode= "isolated"
        # Extract necessary parameters from the request
        # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_apikey'],api_creds_dict['htx_secretkey'])

        # print('data',data)
        # data['ordId'] = 1313907123482300416
        # data['ccy'] = 'BTC-USD'
        print(data['ordId'],data['ccy'])
        order_infos = await tradeApi.get_tpsl_info(instId,
            body = {
            "order_id":data['ordId'],
            "contract_code": data['ccy']
            }
        )
        order_info = order_infos.get('data', [])
        print(order_info)
        return order_info
    
    except Exception as e:
        logger.error(e)

@token_required
@app.route('/htx/swap/get_all_htx_open_orders', methods=['POST'])
async def get_all_htx_open_orders():
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
        instId = data.get('instId','')
        # instId= data["instId"].replace("-SWAP", "")
        tdMode= "cross"
        # Extract necessary parameters from the request
        # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_apikey'],api_creds_dict['htx_secretkey'])

        open_orders = await tradeApi.get_open_orders(
            instId,body = {
            "contract_code": instId
            }
        )
        open_order_data = open_orders.get('data', [])
        print(open_order_data)
        logger.info(open_order_data)
        return open_order_data
    
    except Exception as e:
        logger.error(e)

@token_required
@app.route('/htx/swap/cancel_all_htx_open_order_by_ccy', methods=['POST'])
async def cancel_all_htx_open_order_by_ccy():
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
        # instId= data["instId"].replace("-SWAP", "")
        tdMode= "cross"
        # Extract necessary parameters from the request
        # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_apikey'],api_creds_dict['htx_secretkey'])

        open_orders_request = await tradeApi.revoke_order_all(
            instId,body = {
            "contract_code": instId
            }
        )

        return open_orders_request
    
    except Exception as e:
        logger.error(e)


@token_required
@app.route('/htx/swap/cancel_order_by_id', methods=['POST'])
async def cancel_order_by_id():
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
        instId= instId.replace("-SWAP", "")
        tdMode= "cross"
        # Extract necessary parameters from the request
        # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_apikey'],api_creds_dict['htx_secretkey'])

        revoke_orders = await tradeApi.revoke_order(instId,
            body = {
            "order_id":data['ordId'],
            "contract_code": instId
            }
        )
        revoke_order_data = revoke_orders.get('data', [])
        if len(revoke_order_data['errors']) == 0:
            print('revoked')
        return revoke_order_data
    
    except Exception as e:
        logger.error(e)

@token_required
@app.route('/htx/swap/ammend_order', methods=['POST'])
async def ammend_order():

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
        instId= instId.replace("-SWAP", "")
        tdMode= "cross"
        # Extract necessary parameters from the request
        # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_apikey'],api_creds_dict['htx_secretkey'])

        revoke_orders = await tradeApi.revoke_order(instId,
            body = {
            "order_id":data['ordId'],
            "contract_code": instId
            }
        )
        # print('input',data)
        revoke_order_data = revoke_orders.get('data', [])
        if len(revoke_order_data['errors']) == 0:
            print('revoked')
            instId = data.get("ccy")
            side = data.get("side")
            # since order will always be limit, we set it as limit
            ordType = 'limit'
            
            # Call the asynchronous place_order function
            result = await tradeApi.place_order(instId,body = {
                "contract_code": instId,
                "price": str(data["px"]) if data["px"] else "",
                "created_at": str(datetime.now()),
                "volume": str(data["sz"]),
                "direction": side,
                "offset": "open",
                "lever_rate": 5,
                "order_price_type": ordType,
                "sl_trigger_price":data['stopLoss'] if data['stopLoss'] else "",
                "sl_order_price":data['stopLoss'] if data['stopLoss'] else "",
                "tp_trigger_price":data['takeProfit'] if data['takeProfit'] else "",
                "tp_order_price":data['takeProfit'] if data['takeProfit'] else ""
            })
            print(result)
            print('order placed')
            logger.info("Order request response {}".format(result))
        return revoke_order_data
    
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    app.run(port=6061)