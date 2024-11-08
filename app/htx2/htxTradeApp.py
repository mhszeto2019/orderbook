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
CORS(app)
config_source = 'htx_live_trade'
secretKey = config[config_source]['secretKey']
apiKey = config[config_source]['apiKey']

from HtxOrderClass import HuobiCoinFutureRestTradeAPI

# Initialize the Trade API client
tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",secretKey,apiKey)
import time

# @app.route('/')
# def home():
#     return "Welcome to the OKX Trade API Flask App!"

# # Route to test getting fills
# @app.route('/get_fills', methods=['GET'])
# def get_fills():

#     begin = request.args.get('begin', '1717045609000')
#     end = request.args.get('end', '1717045609100')
#     # print(time.localtime())
#     # current_ts = int(time.time() * 1000)
#     current_ts = time.time() 
#     day_before_ts = current_ts - 86400
#     print(day_before_ts,current_ts)
#     try:
#         fills = tradeApi.get_fills(begin=int(current_ts * 1000), end=int(day_before_ts * 1000))
#         print(fills)
#         return jsonify(fills), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


@app.route('/place_market_order', methods=['POST'])
def place_market_order():
    data = request.get_json()
    
    print(data)

    side = data['side']
    if side == 'buy':
        posSide = 'long'
    else:
        posSide = 'short'

    instId= data["instId"].replace("-SWAP", "")
    print(instId)  # Output: BTC-USD
    tdMode= "cross"
    side= side
    posSide=posSide
    ordType=  data["ordType"]
    sz= str(data["sz"]) 

    result = tradeApi.get_open_orders(
        instId= data["instId"],
        tdMode= "cross", 
        side= side, 
        posSide=posSide, 
        ordType=  data["ordType"],
        sz= str(data["sz"]) 
    )

    # htx_trade_engine.get_open_orders(
#               'BTC-USD',body = {
    #             "contract_code":"BTC-USD",
    #             # "order_id":123456,
    #             "price":60000,
    #             "created_at":str(datetime.datetime.now()),
    #             "volume":1,
    #             "direction":"buy",
    #             "offset":"open",
    #             "lever_rate":1,
    #             "order_price_type":"limit"
    #             })
    print(result)

    if result["code"] == "0":
        print("Successful order request，order_id = ",result["data"][0]["ordId"])

    else:
        print("Unsuccessful order request，error_code = ",result["data"][0]["sCode"], ", Error_message = ", result["data"][0]["sMsg"])

    return result

import datetime
@app.route('/htx/place_limit_order', methods=['POST'])
def place_limit_order():
    data = request.get_json()
    
    side = data['side']
    if side == 'buy':
        posSide = 'long'
    else:
        posSide = 'short'

    instId= data["instId"].replace("-SWAP", "")
    print(instId)  # Output: BTC-USD
    tdMode= "cross"
    side= side
    posSide=posSide
    ordType=  data["ordType"]
    sz= str(data["sz"]) 
    print(data)
    # result = tradeApi.place_order(
    #     instId= data["instId"],
    #     tdMode= "cross", 
    #     side= side, 
    #     posSide=posSide, 
    #     ordType=  data["ordType"],
    #     px= str(data["px"]) if data["px"] else "",
    #     sz= str(data["sz"]) 
    # )

    # Return the result in a valid response format
    result = tradeApi.get_open_orders(  
              instId,body = {
                "contract_code":instId,
                # "order_id":123456,
                "price":str(data["px"]) if data["px"] else "",
                "created_at":str(datetime.datetime.now()),
                "volume":str(data["sz"]),
                "direction":side,
                "offset":"open",
                "lever_rate":3,
                "order_price_type":ordType
                }
    )
    print('result,',result)
    # if result["code"] == "0":
    #     print("Successful order request，order_id = ",result["data"][0]["ordId"])

    # else:
    #     print("Unsuccessful order request，error_code = ",result["data"][0]["sCode"], ", Error_message = ", result["data"][0]["sMsg"])
    # return jsonify(result=result)
    return "Sucess"


    
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
    print(result)
    return result
    
    
@app.route('/cancel_all_orders',methods=['POST'])
def cancel_all_orders():
    order_list = tradeApi.get_orders_history(instType="SPOT")
    data = order_list.get('data',[])
    print(data)
    order_list = []
    for row in data:
        order_list.append({"instId":row['instId'], "ordId":row['ordId']})
    result = tradeApi.cancel_multiple_orders(order_list)
    
    return result

if __name__ == "__main__":
    app.run(port=5025)
   