import asyncio
from okx import Account
import redis
import json
from datetime import datetime
import os
import json
import configparser
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
# print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)
config_source = 'redis'
REDIS_HOST = config[config_source]['host']
REDIS_PORT = config[config_source]['port']
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

config_source = 'okx_live_trade'
apiKey = config[config_source]['apiKey']
secretKey = config[config_source]['secretKey']
passphrase = config[config_source]['passphrase']
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from util import token_required
from util import get_logger 
logger = get_logger(os.path.basename(__file__))

redis_host ='localhost'
redis_port = 6379
redis_db = 0  # Default database
import redis
r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)


from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS
app = Flask(__name__)
CORS(app)

import okx.PublicData as PublicData
# API initialization

from cryptography.fernet import Fernet
import base64



@app.route('/')
def home():
    return "Welcome to the OKX Account position API Flask App!"

@token_required
@app.route('/okx/getfundingrate', methods=['POST'])
def getfundingrate():
    try:
        data = request.get_json()
        # side = data['side']
        username = data.get('username')
        key_string = data.get('redis_key')
        if key_string.startswith("b'") and key_string.endswith("'"):
            cleaned_key_string = key_string[2:-1]
        else:
            cleaned_key_string = key_string  # Fallback if the format is unexpected
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

        publicdataAPI = PublicData.PublicAPI(api_creds_dict['okx_apikey'], api_creds_dict['okx_secretkey'], api_creds_dict['okx_passphrase'], False, '0')
        result = publicdataAPI.get_funding_rate(
           data['ccy']
        )
        if result.get('data'):
            print('success')
        result['ccy'] = data['ccy']
        return result
    except Exception as e:
        print(e)
        return e
    

    # return result


# result = accountAPI.get_account_balance()

# print(result)

# {'code': '0', 'data': [{'adl': '1', 'availPos': '', 'avgPx': '93511.7', 'baseBal': '', 'baseBorrowed': '', 'baseInterest': '', 'bePx': '93567.82385715279', 'bizRefId': '', 'bizRefType': '', 'cTime': '1732693584348', 'ccy': 'BTC', 'clSpotInUseAmt': '', 'closeOrderAlgo': [], 'deltaBS': '', 'deltaPA': '', 'fee': '-0.0000003208154701', 'fundingFee': '0', 'gammaBS': '', 'gammaPA': '', 'idxPx': '93470.8000000000000000', 'imr': '', 'instId': 'BTC-USD-SWAP', 'instType': 'SWAP', 'interest': '', 'last': '93523.8', 'lever': '5', 'liab': '', 'liabCcy': '', 'liqPenalty': '0', 'liqPx': '78261.60025833434', 'margin': '0.0002138769800998', 'markPx': '93516.3', 'maxSpotInUseAmt': '', 'mgnMode': 'isolated', 'mgnRatio': '46.525355824765654', 'mmr': '0.0000042773291929', 'notionalUsd': '100', 'optVal': '', 'pendingCloseOrdLiabVal': '', 'pnl': '0', 'pos': '1', 'posCcy': '', 'posId': '2019681002234920961', 'posSide': 'net', 'quoteBal': '', 'quoteBorrowed': '', 'quoteInterest': '', 'realizedPnl': '-0.0000003208154701', 'spotInUseAmt': '', 'spotInUseCcy': '', 'thetaBS': '', 'thetaPA': '', 'tradeId': '332996199', 'uTime': '1732693584348', 'upl': '0.0000000526022794', 'uplLastPx': '0.0000001383557693', 'uplRatio': '0.0002459464285909', 'uplRatioLastPx': '0.0006468941595617', 'usdPx': '', 'vegaBS': '', 'vegaPA': ''}], 'msg': ''}

if __name__ == "__main__":
    app.run(port = '5001')