from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS

from okx import Trade,SpreadTrading
import os
import json
import configparser
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
# print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)
app = Flask(__name__)
CORS(app)
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

# Initialize the Trade API client
# tradeApi = Trade.TradeAPI(apiKey, secretKey, passphrase, False, '0')
# spreadApi = SpreadTrading.SpreadTradingAPI(apiKey, secretKey, passphrase, False, '0')

import time
from cryptography.fernet import Fernet
import base64
# Decorator function to reinitialize API instances


@app.route('/')
def home():
    return "Welcome to the OKX Trade API Flask App!"

# Route to test getting fills
@app.route('/get_fills', methods=['GET'])
def get_fills():

    begin = request.args.get('begin', '1717045609000')
    end = request.args.get('end', '1717045609100')
    # print(time.localtime())
    # current_ts = int(time.time() * 1000)
    current_ts = time.time() 
    day_before_ts = current_ts - 86400
    # print(day_before_ts,current_ts)
    try:
        fills = tradeApi.get_fills(begin=int(current_ts * 1000), end=int(day_before_ts * 1000))
        print(fills)
        return jsonify(fills), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/okx/swap/place_market_order', methods=['POST'])
@token_required
def place_market_order():
    data = request.get_json()
    side = data['side']
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
        
    # Initialize TradeAPI
    tradeApi = Trade.TradeAPI(api_creds_dict['okx_apikey'], api_creds_dict['okx_secretkey'], api_creds_dict['okx_passphrase'], False, '0')

    result = tradeApi.place_order(
        instId= data["instId"],
        tdMode= "cross", 
        side= side, 
        posSide='', 
        ordType=  data["ordType"],
        sz= str(data["sz"]) 
    )
    result['data'][0]['exchange']='okx'

    if result["code"] == "0":
        result['data'][0]['sCode'] = 200

        # print("Successful order request，order_id = ",result["data"][0]["ordId"])

    else:
        result['data'][0]['sCode'] = 400

        # print("Unsuccessful order request，error_code = ",result["data"][0]["sCode"], ", Error_message = ", result["data"][0]["sMsg"])

    logger.info("Order request resposne {}".format(result))

    return result



@app.route('/okx/swap/place_limit_order', methods=['POST'])
@token_required
def place_limit_order():
    data = request.get_json()
    print(data)

    side = data['side']
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
        
    # Initialize TradeAPI
    tradeApi = Trade.TradeAPI(api_creds_dict['okx_apikey'], api_creds_dict['okx_secretkey'], api_creds_dict['okx_passphrase'], False, '0')

    # tradeApi = Trade.TradeAPI(apiKey, secretKey, passphrase, False, '0')

    result = tradeApi.place_order(
        instId= data["instId"],
        tdMode= "cross", 
        side= side, 
        posSide='', 
        ordType=  data["ordType"],
        px= str(data["px"]) if data["px"] else "",
        sz= str(data["sz"]) 
    )
    result['data'][0]['exchange']='okx'
    
    # code== 0 means success
    if result["code"] == "0":
        # print("Successful order request，order_id = ",result["data"][0]["ordId"])
        result['data'][0]['sCode'] = 200


    else:
        result['data'][0]['sCode'] = 400


        # print("Unsuccessful order request，error_code = ",result["data"][0]["sCode"], ", Error_message = ", result["data"][0]["sMsg"])
    
    # print('result',result)
    logger.info("Order request resposne {}".format(result))

    return result


# not checked
@app.route('/get_order_list', methods=['GET'])
def get_order_list():
    result = tradeApi.get_order_list()
    data = result.get('data',[])
    print(data)
    order_list = []
    for row in data:
        order_list.append({"instId":row['instId'], "ordId":row['ordId']})
    
    return order_list

@app.route('/get_order_history', methods=['GET'])
def get_order_history():
    result = tradeApi.get_orders_history(instType="SPOT")
    print(result)
    return result

@app.route('/cancel_order', methods=['POST'])
def cancel_order():
    data = request.get_json()
    
    print(tradeApi.cancel_order(instId=data['instId'],ordId=data['ordId']))
    

@app.route('/cancel_multiple_orders', methods=['POST'])
def cancel_multiple_order():
    data = request.get_json()
    cancel_orders_list = data
    result = tradeApi.cancel_multiple_orders(cancel_orders_list)
    # print(result)
    return result
    
    
@app.route('/cancel_all_orders',methods=['POST'])
def cancel_all_orders():
    order_list = tradeApi.get_orders_history(instType="SPOT")
    data = order_list.get('data',[])
    # print(data)
    order_list = []
    for row in data:
        order_list.append({"instId":row['instId'], "ordId":row['ordId']})
    result = tradeApi.cancel_multiple_orders(order_list)
    
    return result

if __name__ == "__main__":
    app.run()
    # current_ts = time.time() 
    # day_before_ts = current_ts - 86400
    # print(day_before_ts,current_ts)
    # try:
    #     fills = tradeApi.get_fills(begin=int(current_ts * 1000), end=int(day_before_ts * 1000))
    #     print(fills)
    #     return jsonify(fills), 200
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500

    # # """
    # def test_place_order(self):
    #     attachAlgoOrds = [{'tpTriggerPx': '49000.0', 'tpOrdPx': '-1', 'sz': '1', 'tpTriggerPxType': 'last'}];
    #     print(self.tradeApi.place_order(
    #         "BTC-USDT-SWAP", tdMode="isolated", clOrdId="asCai1234", side='buy', posSide="long", ordType="limit",
    #         sz="1",
    #         px="30000.0",
    #         attachAlgoOrds=attachAlgoOrds)
    #     );
    #
    #     attachAlgoOrds = [{'slTriggerPx': '25000.0', 'slOrdPx': '-1', 'sz': '1', 'slTriggerPxType': 'last'}];
    #     print(self.tradeApi.place_order(
    #         "BTC-USDT-SWAP", tdMode="isolated", clOrdId="asCai1234", side='buy', posSide="long", ordType="limit",
    #         sz="1",
    #         px="30000.0",
    #         attachAlgoOrds=attachAlgoOrds)
    #     );
    #
    #     attachAlgoOrds = [
    #         {
    #             "tpTriggerPxType": "last",
    #             "tpOrdPx": "-1",
    #             "tpTriggerPx": "34000",
    #             "sz": "1"
    #         },
    #         {
    #             "tpTriggerPxType": "last",
    #             "tpOrdPx": "-1",
    #             "tpTriggerPx": "35000",
    #             "sz": "1"
    #         },
    #         {
    #             "slTriggerPxType": "last",
    #             "slOrdPx": "-1",
    #             "slTriggerPx": "20000",
    #             "sz": "3"
    #         }
    #     ]
    #     print(self.tradeApi.place_order(
    #         "BTC-USDT-SWAP", tdMode="isolated", clOrdId="asCai1234", side='buy', posSide="long", ordType="limit",
    #         sz="1",
    #         px="30000.0",
    #         attachAlgoOrds=attachAlgoOrds)
    #     );

    # def test_cancel_order(self):
    #     print(self.tradeApi.cancel_order(instId="ETH-USDT",ordId="480702180748558336"))

    # def test_batch_order(self):
    #     orderData = [{
    #         "instId": "BTC-USDT-SWAP",
    #         "tdMode": "isolated",
    #         "clOrdId": "b15112122",
    #         "side": "buy",
    #         "posSide": "long",
    #         "ordType": "limit",
    #         "px": "30000.0",
    #         "sz": "2",
    #         "attachAlgoOrds": [{'tpTriggerPx': '50000.0', 'tpOrdPx': '-1', 'sz': '1', 'tpTriggerPxType': 'last'}]
    #     },
    #         {
    #             "instId": "BTC-USDT-SWAP",
    #             "tdMode": "isolated",
    #             "clOrdId": "b15112111",
    #             "side": "buy",
    #             "posSide": "long",
    #             "ordType": "limit",
    #             "px": "31000.0",
    #             "sz": "2",
    #             "attachAlgoOrds": [{'tpTriggerPx': '51000.0', 'tpOrdPx': '-1', 'sz': '1', 'tpTriggerPxType': 'last'}]
    #         }
    #     ]
    #
    #     print(self.tradeApi.place_multiple_orders(orderData))

    # 480702180748558336
    # def test_cancel_batch_orders(self):
    #     data=[
    #         {
    #             'instId':"ETH-USDT",
    #             'ordId':"480702885353881600"
    #         },
    #         {
    #             'instId':"BTC-USDT",
    #             'ordId':'480702885353881601'
    #         }
    #     ]
    #     print(self.tradeApi.cancel_multiple_orders(data))
    # def test_amend_order(self):
    #     attachAlgoOrds = [{'attachAlgoId': '672081789170569217', 'newTpTriggerPx': '55000.0'}];
    #     print(self.tradeApi.amend_order("BTC-USDT-SWAP", ordId="672081789170569216", newSz="1",
    #                                     attachAlgoOrds=attachAlgoOrds))

    # def test_amend_order_batch(self):
    #     orderData = [
    #         {
    #             'instId': 'BTC-USDT-SWAP',
    #             'ordId': '672081789170569216',
    #             'newSz': '1',
    #             "attachAlgoOrds": [{'attachAlgoId': '672081789170569217', 'newTpTriggerPx': '53000.0'}]
    #         }
    #     ]
    #
    #     print(self.tradeApi.amend_multiple_orders(orderData))

    # def test_close_all_positions(self):
    #     print(self.tradeApi.close_positions("BTC-USDT",mgnMode="cross"))
    # def test_get_order_info(self):
    #     print(self.tradeApi.get_orders("ETH-USDT","480707205436669952"))
    # def test_get_order_pending(self):
    #     print(self.tradeApi.get_order_list("SPOT"))
    # def test_get_order_history(self):
    #     print(self.tradeApi.get_orders_history("SPOT"))
    # def test_get_order_histry_archive(self):
    #     print(self.tradeApi.orders_history_archive("SPOT"))
    # def test_get_fills(self):
    #     print(self.tradeApi.get_fills(begin='1717045609000',end='1717045609100'))
    # def test_get_fills_history(self):
    #     print(self.tradeApi.get_fills_history("SPOT"))
    # def test_get_order_algo_pending(self):
    #     print(self.tradeApi.order_algos_list('oco'))
    # def test_order_algo(self):
    #     print(self.tradeApi.place_algo_order('BTC-USDT-SWAP', 'cross', side='buy', ordType='trigger', posSide='long',
    #                                      sz='100', triggerPx='22000', triggerPxType	='index', orderPx='-1'))
    # def test_cancel_algos(self):
    #     params = [{
    #     'algoId': '485903392536264704',
    #     'instId': 'BTC-USDT-SWAP'
    #     }]
    #
    #
    #     print(self.tradeApi.cancel_algo_order(params))
    #     def test_cancel_adv_algos(self):
    #     params = [{
    #         'algoId': '485936482235191296',
    #         'instId': 'BTC-USDT-SWAP'
    #     }]
    #
    #     print(self.tradeApi.cancel_advance_algos(params)))
    #     def test_orders_algo_pending(self):
    #     print(self.tradeApi.order_algos_list(ordType='iceberg'))
    #     def test_algo_order_history(self):
    #     print(self.tradeApi.order_algos_history(algoId='485903392536264704',ordType='conditional'))
    #     def test_get_easy_convert_list(self):
    #     print(self.tradeApi.get_easy_convert_currency_list())
    #     def test_easy_convert(self):
    #     print(self.tradeApi.easy_convert(fromCcy=['BTC'],toCcy='OKB'))
    #     def test_get_convert_history(self):
    #     print(self.tradeApi.get_easy_convert_history())
    #     def test_get_oneclick_repay_support_list(self):
    #     print(self.tradeApi.get_oneclick_repay_list('cross'))
    #     def test_oneclick_repay(self):
    #     print(self.tradeApi.oneclick_repay(['BTC'],'USDT'))
    # 485903392536264704
    # 485936482235191296
    # def test_oneclick_repay_history(self):
    #     print(self.tradeApi.oneclick_repay_history())
    # def test_order_algo(self):
    #     print(self.tradeApi.place_algo_order(instId='BTC-USDT-SWAP', tdMode='cross', side='buy', ordType='conditional', \
    #         tpTriggerPx='15', tpOrdPx='18',sz='2'))

    # 581628185981308928
    # def test_get_algo_order_details(self):
    #     print(self.tradeApi.get_algo_order_details(algoId='581628185981308928'))

    # 581628185981308928
    # def test_amend_algo_order(self):
    #     print(self.tradeApi.amend_algo_order(instId='BTC-USDT-SWAP', algoId='581628185981308928',newSz='3'))

    # def test_get_order_history(self):
    #     print(self.tradeApi.get_orders_history(instType="SPOT",begin='1684857629313',end='1684857629313'))

    # def test_get_order_histry_archive(self):
    #     print(self.tradeApi.get_orders_history_archive(instType="SPOT",begin='1684857629313',end='1684857629313'))
    # def test_place_order(self):
    #     print(self.tradeApi.place_order("BTC-USDT", tdMode="cross", clOrdId="asCai1", side="buy", ordType="limit",
    #                                     sz="0.01", px="18000"))
    # def test_batch_order(self):
    #     orderData = [{
    #         "instId": "ETH-USDT",
    #         "tdMode": "cross",
    #         "clOrdId": "b151121",
    #         "side": "buy",
    #         "ordType": "limit",
    #         "px": "2.15",
    #         "sz": "2"
    #     },
    #         {
    #             "instId": "BTC-USDT",
    #             "tdMode": "cross",
    #             "clOrdId": "b152233",
    #             "side": "buy",
    #             "ordType": "limit",
    #             "px": "2.15",
    #             "sz": "2"
    #         }]
    #     print(self.tradeApi.place_multiple_orders(orderData))

    # 581616258865516544
    # 581616258865516545
    # def test_amend_order(self):
    #     print(self.tradeApi.amend_order("BTC-USDT", ordId="581616258865516544", newSz="0.03"))
    # def test_amend_order_batch(self):
    #     orderData = [
    #         {
    #             'instId': 'ETH-USDT',
    #             'ordId': '581616258865516544',
    #             'newSz': '0.02'
    #         },
    #         {
    #             'instId': 'BTC-USDT',
    #             'ordId': '581616258865516545',
    #             'newPx': '3.0'
    #         }
    #     ]
    #     print(self.tradeApi.amend_multiple_orders(orderData))

    # def test_order_algo(self):
    #
    #     print(self.tradeApi.place_algo_order(instId='BTC-USDT-SWAP', tdMode='cross', side='buy', ordType='conditional', \
    #                                          tpTriggerPx='15', tpOrdPx='18', sz='2',algoClOrdId='7678687',quickMgnType='manual'))

    # def test_order_algos_list(self):
    #     print(self.tradeApi.order_algos_list(ordType='conditional'))

    # def test_order_algo(self):
    #     print(self.tradeApi.place_order(instId='BTC-USDT-SWAP', tdMode='cross', side='buy',px='121',sz='2',
    #                                     clOrdId='234234565535',ordType='market'))
    # def test_close_all_positions(self):
    #     print(self.tradeApi.close_positions(instId="BTC-USDT-SWAP", mgnMode="cross",clOrdId='1213124'))

