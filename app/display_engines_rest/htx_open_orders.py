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
import datetime
import asyncio
import base64
from cryptography.fernet import Fernet
# Initialize the Trade API client
# tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",secretKey,apiKey)

@token_required
@app.route('/htx/swap/get_order_info', methods=['POST'])
async def get_order_info():
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
        
    try:

        # Data received from the client (assuming JSON body)
        instId = data.get('ccy','')
        instId= instId.replace("-SWAP", "")
        tdMode= "cross"
        # Extract necessary parameters from the request
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
        print('data',data)
        order_infos = await tradeApi.get_order_info(instId,
            body = {
            "order_id":data['ordId'],
            "contract_code": instId
            }
        )
        print(order_infos)
        order_info = order_infos.get('data', [])
        
        return order_info
    
    except Exception as e:
        print(e)

@token_required
@app.route('/htx/swap/get_tpsl_info', methods=['POST'])
async def get_tpsl_info():
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
        
    try:

        # Data received from the client (assuming JSON body)
        instId = data.get('ccy','')
        instId= instId.replace("-SWAP", "")
        tdMode= "isolated"
        # Extract necessary parameters from the request
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
        # print('data',data)
        data['ordId'] = 1313907123482300416
        data['ccy'] = 'BTC-USD'
        print(data['ordId'],data['ccy'])
        order_infos = await tradeApi.get_tpsl_info(instId,
            body = {
            "order_id":data['ordId'],
            "contract_code": data['ccy']
            }
        )
        print(order_infos)
        order_info = order_infos.get('data', [])
        
        return order_info
    
    except Exception as e:
        print(e)

@token_required
@app.route('/htx/swap/get_all_htx_open_orders', methods=['POST'])
async def get_all_htx_open_orders():
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
        
    try:
        # Data received from the client (assuming JSON body)
        instId = data.get('instId','')
        # instId= data["instId"].replace("-SWAP", "")
        tdMode= "cross"
        # Extract necessary parameters from the request
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
        open_orders = await tradeApi.get_open_orders(
            instId,body = {
            "contract_code": instId
            }
        )
        open_order_data = open_orders.get('data', [])
        print(open_order_data)
        return open_order_data
    
    except Exception as e:
        print(e)

@token_required
@app.route('/htx/swap/cancel_all_htx_open_order_by_ccy', methods=['POST'])
async def cancel_all_htx_open_order_by_ccy():
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
        
    try:

        # Data received from the client (assuming JSON body)
        instId = data.get('ccy','')
        # instId= data["instId"].replace("-SWAP", "")
        tdMode= "cross"
        # Extract necessary parameters from the request
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
        open_orders_request = await tradeApi.revoke_order_all(
            instId,body = {
            "contract_code": instId
            }
        )

        return open_orders_request
    
    except Exception as e:
        print(e)


@token_required
@app.route('/htx/swap/cancel_order_by_id', methods=['POST'])
async def cancel_order_by_id():
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
        
    try:

        # Data received from the client (assuming JSON body)
        instId = data.get('ccy','')
        instId= instId.replace("-SWAP", "")
        tdMode= "cross"
        # Extract necessary parameters from the request
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
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
        print(e)



@token_required
@app.route('/htx/swap/ammend_order', methods=['POST'])
async def ammend_order():
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
        
    try:
        # delete order and create again 

        # Data received from the client (assuming JSON body)
        instId = data.get('ccy','')
        instId= instId.replace("-SWAP", "")
        tdMode= "cross"
        # Extract necessary parameters from the request
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
        revoke_orders = await tradeApi.revoke_order(instId,
            body = {
            "order_id":data['ordId'],
            "contract_code": instId
            }
        )
        print(data)
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
                "created_at": str(datetime.datetime.now()),
                "volume": str(data["sz"]),
                "direction": side,
                "offset": "open",
                "lever_rate": 5,
                "order_price_type": ordType
            })
            print(result)
            print('order placed')
            logger.info("Order request response {}".format(result))
        return revoke_order_data
    
    except Exception as e:
        print(e)


if __name__ == "__main__":
    app.run(port=6061)