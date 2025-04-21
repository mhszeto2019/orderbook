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

# Constants for order configurations
ORDER_PRICE_TYPE = "optimal_20"
LEVER_RATE = 5
OFFSET_OPEN = "open"
OFFSET_CLOSE = "close"

# Helper function to handle placing orders
async def place_order(tradeApi, instId, volume, direction, offset):
    return await tradeApi.place_order(
        instId,
        body={
            "contract_code": instId,
            "created_at": datetime.datetime.now().isoformat(),
            "volume": str(volume),
            "direction": direction,
            "offset": offset,
            "lever_rate": LEVER_RATE,
            "order_price_type": ORDER_PRICE_TYPE
        }
    )

@token_required
@app.route('/htx/swap/place_market_order', methods=['POST'])
async def place_market_order():
    data = request.get_json()
    side = data['side']
    username = data.get('username')
    # Get the order data from the request
    # okx_secretkey_apikey_passphrase = r.get('user:test123d:api_credentials"')
    key_string = data.get('redis_key')
    # cleaned_key_string = key_string.strip("b'")
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
        instId= data["instId"].replace("-SWAP", "")
        tdMode= "cross"
        side= side
        posSide='long'
        sz_int = int(data['sz'])
        sz= str(data["sz"]) 
        # Extract necessary parameters from the request
        # instId = data.get("instId")
        side = data.get("side")
        # ordType = data.get("ordType")
        if data['ordType'] == 'market':
            ordType = 'optimal_20'
        data["ordType"]=  'optimal_20'
        # print(instId)
       
        # Initialize TradeAPI
        # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_apikey'],api_creds_dict['htx_secretkey'])

        positions = await tradeApi.get_positions(instId,body = {
            "contract_code": instId
            }
            )
        position_data = positions.get('data', [])

    


        # Check if position_data has at least one item to avoid IndexError
        if position_data:

            print(f"Position data:{position_data}")
            # Extract availability and direction with default values
            availability = int(position_data[0].get('volume', 0))
            direction = position_data[0].get('direction', None)
        else:
            # If no position data is found, set defaults for availability and direction
            availability = 0
            direction = None
        
    #  # Determine the order logic
        if direction and side == direction:
            result = await place_order(tradeApi, instId, sz_int, side, OFFSET_OPEN)
        elif direction and sz_int > availability:
            # Close the available positions first
            await place_order(tradeApi, instId, availability, side, OFFSET_CLOSE)
            result = await place_order(tradeApi, instId, sz_int - availability, side, OFFSET_OPEN)
        elif direction and sz_int <= availability:
            # Close the positions directly
            result = await place_order(tradeApi, instId, sz_int, side, OFFSET_CLOSE)
        else:
            # Opening a new position
            result = await place_order(tradeApi, instId, sz_int, side, OFFSET_OPEN)

        logger.info("HTX MARKET Order request response {}".format(result))

        if result['status'] == 'error':
            return jsonify({"error": "Bad Requestss"}), 400  # Th
        return jsonify(result),200

    except Exception as e:
        return jsonify(result), 500


import datetime
@token_required
@app.route('/htx/swap/place_limit_order', methods=['POST'])
async def place_limit_order():
    data = request.get_json()
    
    username = data.get('username')
    # Get the order data from the request
    # okx_secretkey_apikey_passphrase = r.get('user:test123d:api_credentials"')
    key_string = data.get('redis_key')
    cleaned_key_string = key_string.strip("b'")

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
        print(f"API credentials for {username}", api_creds_dict)

        
    side = data['side']
    if side == 'buy':
        posSide = 'long'
    else:
        posSide = 'short'

    tdMode= "cross"
    sz= str(data["sz"]) 
    try:

        # Extract necessary parameters from the request
        if 'SWAP' in data['instId']:
            instId=  data["instId"].replace("-SWAP", "")
        else:
            instId = data.get("instId")
        side = data.get("side")
        ordType = data.get("ordType")
        # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_apikey'],api_creds_dict['htx_secretkey'])
        positions = await tradeApi.get_positions(instId,body = {
            "contract_code": instId
            }
            )
        
        # print("POSITIONSSSS",positions)
        position_data = positions.get('data', [])

        # Check if position_data has at least one item to avoid IndexError
        if position_data:
            # Extract availability and direction with default values
            availability = int(position_data[0].get('available', 0))
            direction = position_data[0].get('direction', None)
        else:
            # If no position data is found, set defaults for availability and direction
            availability = 0
            direction = None
        # Data received from the client (assuming JSON body)


        print('data sz', data['sz'])

        if direction and side == direction or availability == 0:
            # same direction so we just add on
            # print('same direction')
            result = await tradeApi.place_order(instId,body = {
            "contract_code": instId,
            "price": str(data["px"]) if data["px"] else "",
            "created_at": str(datetime.datetime.now()),
            "volume": str(data["sz"]),
            "direction": side,
            "offset": "open",
            "lever_rate": 5,
            "order_price_type": "limit"         }
            )
        
        else: 
            if direction != None and int(data["sz"]) > availability:
                # print('first close the available positions - close the long pos')
                result = await tradeApi.place_order(instId,body = {
                "contract_code": instId,
                "price": str(data["px"]) if data["px"] else "",
                "created_at": str(datetime.datetime.now()),
                "volume": str(availability) ,
                "direction": side,
                "offset": "close",
                "lever_rate": 5,
                "order_price_type": "limit"         }
                )
                result = await tradeApi.place_order(instId,body = {
                "contract_code": instId,
                "price": str(data["px"]) if data["px"] else "",
                "created_at": str(datetime.datetime.now()),
                "volume": str(data["sz"] - availability),
                "direction": side,
                "offset": "open",
                "lever_rate": 5,
                "order_price_type": "limit"         }
                )
                # print('second carry on with the trade with sz = sz - availability - buy short')
            elif direction != None and int(data["sz"]) <= availability:
                # print('close positions')
                result = await tradeApi.place_order(instId,body = {
                "contract_code": instId,
                "price": str(data["px"]) if data["px"] else "",
                "created_at": str(datetime.datetime.now()),
                "volume": str(data["sz"]) ,
                "direction": side,
                "offset": "close",
                "lever_rate": 5,
                "order_price_type": "limit"         }
                )
            else:
                print('opening a new position, ',instId)
                result = await tradeApi.place_order(instId,body = {
                "contract_code": instId,
                "price": str(data["px"]) if data["px"] else "",
                "created_at": str(datetime.datetime.now()),
                "volume": str(data["sz"]) ,
                "direction": side,
                "offset": "open",
                "lever_rate": 5,
                "order_price_type": "limit"        }
                )




        # # Call the asynchronous place_order function
        # result = await tradeApi.place_order(instId,body = {
        #     "contract_code": instId,
        #     "price": str(data["px"]) if data["px"] else "",
        #     "created_at": str(datetime.datetime.now()),
        #     "volume": str(data["sz"]),
        #     "direction": side,
        #     "offset": "open",
        #     "lever_rate": 5,
        #     "order_price_type": ordType
        # })
        logger.info("Order request response {}".format(result))
        print('ending here')
        print(result)
        if 'status' in result and result['status'] == 'error':
            return jsonify({"error": "Bad Requestss"}), 400  # Th
        print('ending here2')
        
        return jsonify(result),200

    except Exception as e:
        return jsonify(result), 500

# import datetime
# @token_required
# @app.route('/htx/swap/place_limit_order', methods=['POST'])
# async def place_limit_order():
#     data = request.get_json()
    
#     username = data.get('username')
#     # Get the order data from the request
#     # okx_secretkey_apikey_passphrase = r.get('user:test123d:api_credentials"')
#     key_string = data.get('redis_key')
#     cleaned_key_string = key_string.strip("b'")

#     # Now decode the base64 string into bytes
#     key_bytes = base64.urlsafe_b64decode(cleaned_key_string)
#     key_bytes = cleaned_key_string.encode('utf-8')
#     # You can now use the key with Fernet
#     cipher_suite = Fernet(key_bytes)
    
#     cache_key = f"user:{username}:api_credentials"
#     # Fetch the encrypted credentials from Redis
#     encrypted_data = r.get(cache_key)   
    
#     if encrypted_data:
#     # Decrypt the credentials
#         decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
#         api_creds_dict = json.loads(decrypted_data)
#         print(f"API credentials for {username}", api_creds_dict)
#     print(encrypted_data)
#     side = data['side']
#     if side == 'buy':
#         posSide = 'long'
#     else:
#         posSide = 'short'

#     tdMode= "cross"
#     sz= str(data["sz"]) 
#     try:
#         # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
#         tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_apikey'],api_creds_dict['htx_secretkey'])

#         # Data received from the client (assuming JSON body)
#         # Extract necessary parameters from the request
#         if 'SWAP' in data['instId']:
#             instId=  data["instId"].replace("-SWAP", "")
#         else:
#             instId = data.get("instId")
#         side = data.get("side")
#         ordType = data.get("ordType")
#         print(instId,side,ordType)
#         # Call the asynchronous place_order function
#         result = await tradeApi.place_order(instId,body = {
#             "contract_code": instId,
#             "price": str(data["px"]) if data["px"] else "",
#             "created_at": str(datetime.datetime.now()),
#             "volume": str(data["sz"]),
#             "direction": side,
#             "offset": "open",
#             "lever_rate": 5,
#             "order_price_type": ordType
#         })
#         logger.info("Order request response {}".format(result))
#         print('ending here')
#         print(result)
#         if 'status' in result and result['status'] == 'error':
#             return jsonify({"error": "Bad Requestss"}), 400  # Th
#         print('ending here2')
        
#         return jsonify(result),200

#     except Exception as e:
#         return jsonify(result), 500




@token_required
@app.route('/htx/futures/place_limit_order', methods=['POST'])
async def place_limit_contract_order():
    data = request.get_json()
    side = data['side']
    username = data.get('username')
    # Get the order data from the request
    # okx_secretkey_apikey_passphrase = r.get('user:test123d:api_credentials"')
    key_string = data.get('redis_key')
    # cleaned_key_string = key_string.strip("b'")
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
        print(f"API credentials for {username}", api_creds_dict)
        
       
    try:
        # Data received from the client (assuming JSON body)
        instId = data.get("instId")
        side = data.get("side")
        ordType = data.get("ordType")
        contract_type = data.get('contract_type')
        # print(instId,side,ordType,contract_type)
        side= side
        sz_int = int(data['sz'])
    
        # Extract necessary parameters from the request
        instId = data.get("instId")
        side = data.get("side")

        if data['ordType'] == 'market':
            ordType = 'optimal_20'
        data["ordType"]=  'optimal_20'
        # Initialize TradeAPI
        # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_apikey'],api_creds_dict['htx_secretkey'])

        # print('GETING POSITIONS')
        positions = await tradeApi.get_contract_positions(instId,body = {
            "symbol": instId
            }
            )
        
        # print("POSITIONSSSS",positions)
        position_data = positions.get('data', [])

        # Check if position_data has at least one item to avoid IndexError
        if position_data:
            # Extract availability and direction with default values
            availability = int(position_data[0].get('available', 0))
            direction = position_data[0].get('direction', None)
        else:
            # If no position data is found, set defaults for availability and direction
            availability = 0
            direction = None

        if direction and side == direction :
            # same direction so we just add on
            print('same direction')

            result = await tradeApi.place_contract_order(instId,body = {
            "symbol": instId,
            "price": str(data["px"]) if data["px"] else "",
            "contract_type":contract_type,
            "created_at": str(datetime.datetime.now()),
            "volume": str(data["sz"]),
            "direction": side,
            "offset": "open",
            "lever_rate": 5,
            "order_price_type": ordType        }
            )
        else: 
            if direction != None and sz_int > availability:
                print('first close the available positions - close the long pos')
                result = await tradeApi.place_contract_order(instId,body = {
                "symbol": instId,
                "price": str(data["px"]) if data["px"] else "",

                "contract_type":contract_type,
                "created_at": str(datetime.datetime.now()),
                "volume": str(availability) ,
                "direction": side,
                "offset": "close",
                "lever_rate": 5,
                "order_price_type": ordType        }
                )
                print('second carry on with the trade with sz = sz - availability - buy short')

                result = await tradeApi.place_contract_order(instId,body = {
                "symbol": instId,
                "price": str(data["px"]) if data["px"] else "",

                "contract_type":contract_type,
                "created_at": str(datetime.datetime.now()),
                "volume": str(sz_int - availability),
                "direction": side,
                "offset": "open",
                "lever_rate": 5,
                "order_price_type": ordType        }
                )
            elif direction != None and sz_int <= availability:
                print('close positions')
                result = await tradeApi.place_contract_order(instId,body = {
                "symbol": instId,
                "price": str(data["px"]) if data["px"] else "",

                "contract_type":contract_type,
                "created_at": str(datetime.datetime.now()),
                "volume": str(sz_int) ,
                "direction": side,
                "offset": "close",
                "lever_rate": 5,
                "order_price_type": ordType        }
                )
            else:
                print('opening a new position ')
                result = await tradeApi.place_contract_order(instId,body = {
                "symbol": instId,
                "price": str(data["px"]) if data["px"] else "",

                "contract_type":contract_type,
                "created_at": str(datetime.datetime.now()),
                "volume": str(sz_int) ,
                "direction": side,
                "offset": "open",
                "lever_rate": 5,
                "order_price_type": ordType        }
                )
        print(result)
        logger.info("Order request response {}".format(result))

        if result['status'] == 'error':
            return jsonify({"error": "Bad Requestss"}), 400  # Th
        return jsonify(result),200
    except Exception as e:
        return jsonify(result), 500
    

@token_required
@app.route('/htx/futures/place_market_order', methods=['POST'])
async def place_market_contract_order():
    data = request.get_json()
    side = data['side']
    username = data.get('username')
    # Get the order data from the request
    # okx_secretkey_apikey_passphrase = r.get('user:test123d:api_credentials"')
    key_string = data.get('redis_key')
    # cleaned_key_string = key_string.strip("b'")
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
        print(f"API credentials for {username}", api_creds_dict)
        
       
    try:
        # Data received from the client (assuming JSON body)
        instId = data.get("instId")
        side = data.get("side")
        ordType = data.get("ordType")
        contract_type = data.get('contract_type')
        print(instId,side,ordType,contract_type)
        side= side
        sz_int = int(data['sz'])
    
        # Extract necessary parameters from the request
        instId = data.get("instId")
        side = data.get("side")

        if data['ordType'] == 'market':
            ordType = 'optimal_20'
        data["ordType"]=  'optimal_20'
       
        # Initialize TradeAPI
        # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_apikey'],api_creds_dict['htx_secretkey'])


        positions = await tradeApi.get_contract_positions(instId,body = {
            "contract_code": instId
            }
            )
        
        # print("POSITIONSSSS",positions)
        position_data = positions.get('data', [])

        # Check if position_data has at least one item to avoid IndexError
        if position_data:
            # Extract availability and direction with default values
            availability = int(position_data[0].get('available', 0))
            direction = position_data[0].get('direction', None)
        else:
            # If no position data is found, set defaults for availability and direction
            availability = 0
            direction = None

        
        if direction and side == direction :
            # same direction so we just add on
            print('same direction')

           

            result = await tradeApi.place_contract_order(instId,body = {
            "symbol": instId,
            "contract_type":contract_type,
            "created_at": str(datetime.datetime.now()),
            "volume": str(data["sz"]),
            "direction": side,
            "offset": "open",
            "lever_rate": 5,
            "order_price_type": ordType        }
            )
        else: 
            if direction != None and sz_int > availability:
                print('first close the available positions - close the long pos')
                result = await tradeApi.place_contract_order(instId,body = {
                "symbol": instId,
                "contract_type":contract_type,
                "created_at": str(datetime.datetime.now()),
                "volume": str(availability) ,
                "direction": side,
                "offset": "close",
                "lever_rate": 5,
                "order_price_type": ordType        }
                )
                result = await tradeApi.place_contract_order(instId,body = {
                "symbol": instId,
                "contract_type":contract_type,
                "created_at": str(datetime.datetime.now()),
                "volume": str(sz_int - availability),
                "direction": side,
                "offset": "open",
                "lever_rate": 5,
                "order_price_type": ordType        }
                )
                print('second carry on with the trade with sz = sz - availability - buy short')
            elif direction != None and sz_int <= availability:
                print('close positions')
                result = await tradeApi.place_contract_order(instId,body = {
                "symbol": instId,
                "contract_type":contract_type,
                "created_at": str(datetime.datetime.now()),
                "volume": str(sz_int) ,
                "direction": side,
                "offset": "close",
                "lever_rate": 5,
                "order_price_type": ordType        }
                )
            else:
                print('opening a new position ')
                result = await tradeApi.place_contract_order(instId,body = {
                "symbol": instId,
                "contract_type":contract_type,
                "created_at": str(datetime.datetime.now()),
                "volume": str(sz_int) ,
                "direction": side,
                "offset": "open",
                "lever_rate": 5,
                "order_price_type": ordType        }
                )
        print(result)
        logger.info("Order request response {}".format(result))

        if result['status'] == 'error':
            return jsonify({"error": "Bad Requestss"}), 400  # Th
        return jsonify(result),200

    except Exception as e:
        return jsonify(result), 500

# @app.route('/get_order_list', methods=['GET'])
# def get_order_list():
#     result = tradeApi.get_order_list()
#     data = result.get('data',[])
#     print(data)
#     order_list = []
#     for row in data:
#         order_list.append({"instId":row['instId'], "ordId":row['ordId']})
    
#     return order_list

# @app.route('/get_order_history', methods=['GET'])
# def get_order_history():
#     result = tradeApi.get_orders_history(instType="SPOT")
#     print(result)
#     return result


# # not tested yet
# @app.route('/cancel_order', methods=['POST'])
# def cancel_order():
#     data = request.get_json()
    
#     print(tradeApi.cancel_order(instId=data['instId'],ordId=data['ordId']))
    

# @app.route('/cancel_multiple_orders', methods=['POST'])
# def cancel_multiple_order():
#     data = request.get_json()
#     cancel_orders_list = data
#     result = tradeApi.cancel_multiple_orders(cancel_orders_list)
#     print(result)
#     return result
    
# @app.route('/cancel_all_orders',methods=['POST'])
# def cancel_all_orders():
#     order_list = tradeApi.get_orders_history(instType="SPOT")
#     data = order_list.get('data',[])
#     print(data)
#     order_list = []
#     for row in data:
#         order_list.append({"instId":row['instId'], "ordId":row['ordId']})
#     result = tradeApi.cancel_multiple_orders(order_list)
    
#     return result

if __name__ == "__main__":
    app.run(port=5081)
   