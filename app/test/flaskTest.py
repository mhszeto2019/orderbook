import asyncio
import threading
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS  # Import CORS
import asyncio


import os
from okx.websocket.WsPrivateAsync import WsPrivateAsync

import json
import configparser
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*",async_mode='gevent')
CORS(app)  # Enable CORS for all origins
<<<<<<< HEAD

config_source = 'okx_live_trade'
apiKey = config[config_source]['apiKey']
secretKey = config[config_source]['secretKey']
passphrase = config[config_source]['passphrase']


=======
>>>>>>> 4d917a6 (working flaskTest but need to fix unsubscribe)
import random
def privateCallback(message):
    print("privateCallback", message)

def emitToclient(message):
<<<<<<< HEAD
    print("MESSAGE",message)
    json_msg = json.loads(message)
    event = json_msg.get('event',None)
    if json_msg.get('arg'):
        channel = json_msg.get('arg',"Loading ...")['channel']
        data =  json_msg.get('data',[])
        # we cant handle data here because components are all in lists and we dont want to repeat for loop in backend
        if data:
            if channel == "balance_and_position":
                print('data',data,type(data[0]))
                data_to_client = {"event":None,"channel":channel,"data":data}
            elif channel == "positions":
                data_to_client = {"event":None,"channel":channel,"data":data}
            
            
            else:
                print('data2',data)
                data_to_client = {"event":None,"channel":channel,"data":data}

        data_to_client = {"event":None,"channel":channel,"data":data}
        
    else:
        data_to_client = {"event":f"{event}","data":"loading"}
    # sending json object to client
    

    data_to_client_fake2 = dict({
            "channel": "positions",
            "data": [
                    {
                    "adl":"1",
                    "availPos":"1",
                    "avgPx":"2566.31",
                    #   "cTime":"1619507758793",
                    "ccy":"ETH",
                    "instId":"ETH-USD-210430",
                    "instType":"FUTURES",
                    #   "interest":"0",
                    "idxPx":"2566.13",
                    "last":"2566.22",
                    #   "usdPx":"",
                    "bePx":"2353.949",
                    "lever":"10",
                    "liqPx":"2352.8496681818233",
                    "markPx":"2353.849",
                    "margin":"0.0003896645377994",
                    "mgnMode":"isolated",
                    "mgnRatio":"11.731726509588816",
                    "mmr":"0.0000311811092368",
                    "notionalUsd":"2276.2546609009605",
                    #   "optVal":"",
                      "pTime":"1619507761462",
                    #   "pendingCloseOrdLiabVal":"0.1",
                    #   "pos":"1",
                    #   "posId":"307173036051017730",
                    "posSide":"long",
                    "tradeId":"109844",
                      "uTime":"1619507761462",
                    "upl":"-0.0000009932766034",
                    "uplLastPx":"-0.0000009932766034",
                    "uplRatio":"-0.0025490556801078",
                    "uplRatioLastPx":"-0.0025490556801078",
                    "realizedPnl":"0.001",
                    "pnl":"0.0011",
                    "fee":"-0.0001"
                
                    },
                    {
                    "adl":"1",
                    "availPos":"1",
                    "avgPx":"2566.31",
                    #   "cTime":"1619507758793",
                    "ccy":"ETH",
                    "instId":"ETH-USD-210430",
                    "instType":"FUTURES",
                    #   "interest":"0",
                    "idxPx":"2566.13",
                    "last":"2566.22",
                    #   "usdPx":"",
                    "bePx":"2353.949",
                    "lever":"10",
                    "liqPx":"2352.8496681818233",
                    "markPx":"2353.849",
                    "margin":"0.0003896645377994",
                    "mgnMode":"isolated",
                    "mgnRatio":"11.731726509588816",
                    "mmr":"0.0000311811092368",
                    "notionalUsd":"2276.2546609009605",
                    #   "optVal":"",
                      "pTime":"1619507761462",
                    #   "pendingCloseOrdLiabVal":"0.1",
                    #   "pos":"1",
                    #   "posId":"307173036051017730",
                    "posSide":"long",
                    "tradeId":"109844",
                      "uTime":"1619507761462",
                    "upl":"-0.0000009932766034",
                    "uplLastPx":"-0.0000009932766034",
                    "uplRatio":"-0.0025490556801078",
                    "uplRatioLastPx":"-0.0025490556801078",
                    "realizedPnl":"0.001",
                    "pnl":"0.0011",
                    "fee":"-0.0001"
                
                    }
            ]
            }
        )
    data_to_client_fake = dict({
        "channel":"orders",
        "data": [
            {
                "accFillSz": "0.001",
                "algoClOrdId": "",
                "algoId": "",
                "amendResult": "",
                "amendSource": "",
                "avgPx": "31527.1",
                "cancelSource": "",
                "category": "normal",
                "ccy": "",
                "clOrdId": "",
                "code": "0",
                "cTime": "1654084334977",
                "execType": "M",
                "fee": "-0.02522168",
                "feeCcy": "USDT",
                "fillFee": "-0.02522168",
                "fillFeeCcy": "USDT",
                "fillNotionalUsd": "31.50818374",
                "fillPx": "31527.1",
                "fillSz": "0.001",
                "fillPnl": "0.01",
                "fillTime": "1654084353263",
                "fillPxVol": "",
                "fillPxUsd": "",
                "fillMarkVol": "",
                "fillFwdPx": "",
                "fillMarkPx": "",
                "instId": "BTC-USDT",
                "instType": "SPOT",
                "lever": "0",
                "msg": "",
                "notionalUsd": "31.50818374",
                "ordId": "452197707845865472",
                "ordType": "limit",
                "pnl": "0",
                "posSide": "",
                "px": "31527.1",
                "pxUsd":"",
                "pxVol":"",
                "pxType":"",
                "quickMgnType": "",
                "rebate": "0",
                "rebateCcy": "BTC",
                "reduceOnly": "false",
                "reqId": "",
                "side": "sell",
                "attachAlgoClOrdId": "",
                "slOrdPx": "",
                "slTriggerPx": "",
                "slTriggerPxType": "last",
                "source": "",
                "state": "filled",
                "stpId": "",
                "stpMode": "",
                "sz": "0.001",
                "tag": "",
                "tdMode": "cash",
                "tgtCcy": "",
                "tpOrdPx": "",
                "tpTriggerPx": "",
                "tpTriggerPxType": "last",
                "attachAlgoOrds": [],
                "tradeId": "242589207",
                "lastPx": "38892.2",
                "uTime": "1654084353264",
                "isTpLimit": "false",
                "linkedAlgoOrd": {
                    "algoId": ""
                }
            },
            {
                "accFillSz": "0.001",
                "algoClOrdId": "",
                "algoId": "",
                "amendResult": "",
                "amendSource": "",
                "avgPx": "31527.1",
                "cancelSource": "",
                "category": "normal",
                "ccy": "",
                "clOrdId": "",
                "code": "0",
                "cTime": "1654084334977",
                "execType": "M",
                "fee": "-0.02522168",
                "feeCcy": "USDT",
                "fillFee": "-0.02522168",
                "fillFeeCcy": "USDT",
                "fillNotionalUsd": "31.50818374",
                "fillPx": "31527.1",
                "fillSz": "0.001",
                "fillPnl": "0.01",
                "fillTime": "1654084353263",
                "fillPxVol": "",
                "fillPxUsd": "",
                "fillMarkVol": "",
                "fillFwdPx": "",
                "fillMarkPx": "",
                "instId": "BTC-USDT",
                "instType": "SPOT",
                "lever": "0",
                "msg": "",
                "notionalUsd": "31.50818374",
                "ordId": "452197707845865472",
                "ordType": "limit",
                "pnl": "0",
                "posSide": "",
                "px": "31527.1",
                "pxUsd":"",
                "pxVol":"",
                "pxType":"",
                "quickMgnType": "",
                "rebate": "0",
                "rebateCcy": "BTC",
                "reduceOnly": "false",
                "reqId": "",
                "side": "sell",
                "attachAlgoClOrdId": "",
                "slOrdPx": "",
                "slTriggerPx": "",
                "slTriggerPxType": "last",
                "source": "",
                "state": "filled",
                "stpId": "",
                "stpMode": "",
                "sz": "0.001",
                "tag": "",
                "tdMode": "cash",
                "tgtCcy": "",
                "tpOrdPx": "",
                "tpTriggerPx": "",
                "tpTriggerPxType": "last",
                "attachAlgoOrds": [],
                "tradeId": "242589207",
                "lastPx": "38892.2",
                "uTime": "1654084353264",
                "isTpLimit": "false",
                "linkedAlgoOrd": {
                    "algoId": ""
                }
            }
        ]}
    )
    
    import random
    data_to_test = []
    data_to_test.append(data_to_client_fake)
    data_to_test.append(data_to_client_fake2)
    # data_to_test.append(data_to_client)
    # TESTING
    # import time
    # time.sleep(5)
    # num =random.randint(0,1)
    # chosen_data = data_to_test[num]
    # print(chosen_data)
    socketio.emit('oms',data_to_client)
=======
    # print(message)
    json_msg = json.loads(message)
    data_to_client = "Loading ..."
    
    if json_msg.get('arg',None):
        print(json_msg.get('event',None))
        
        channel = json_msg.get('arg',"logging")['channel']
        print(channel) 
        data_to_client = json_msg.get('data')
#     message ={
#     "arg": {
#         "channel": "balance_and_position",
#         "uid": "77982378738415879"
#     },
#     "data": [{
#         "pTime": "1597026383085",
#         "eventType": "snapshot",
#         "balData": [{
#             "ccy": "BTC",
#             "cashBal": "1",
#             "uTime": "1597026383085"
#         }],
#         "posData": [{
#             "posId": "1111111111",
#             "tradeId": "2",
#             "instId": "BTC-USD-191018",
#             "instType": "FUTURES",
#             "mgnMode": "cross",
#             "posSide": "long",
#             "pos": f'{random.randint(3, 9)}',
#             "ccy": "BTC",
#             "posCcy": "",
#             "avgPx": "3320",
#             "uTIme": f'{random.randint(3, 9)}'
#         }],
#         "trades": [{
#             "instId": "BTC-USD-191018",
#             "tradeId": "2",
#         }]
#     }]
# }
        
        socketio.emit(channel,json.dumps(data_to_client))

config_source = 'okx_live_trade'

apiKey = config[config_source]['apiKey']
secretKey = config[config_source]['secretKey']
passphrase = config[config_source]['passphrase']
>>>>>>> 4d917a6 (working flaskTest but need to fix unsubscribe)

ws = None

loop = asyncio.get_event_loop()  
<<<<<<< HEAD
=======

# Queue to handle messages (optional, but useful if multiple consumers are needed)
>>>>>>> 4d917a6 (working flaskTest but need to fix unsubscribe)
message_queue = asyncio.Queue()

# WebSocket listener function
async def listen_to_websocket():
    global ws
    while True:
        try:
            message = await ws.recv()  # Ensure only one recv() is called
            await message_queue.put(message)  # Optionally, queue the message
            await handle_message(message)  # Process each message
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

# Function to handle received WebSocket messages
async def handle_message(message):
    # Process the incoming message
    print(f"Received message: {message}")
    # You can add additional processing logic here, e.g., logging, database, etc.
<<<<<<< HEAD

# Your WebSocket connection and subscription logic
async def main():
    global ws
    url = "wss://ws.okx.com:8443/ws/v5/private"
    ws = WsPrivateAsync(
        apiKey = apiKey,
        passphrase=passphrase,
        secretKey=secretKey,
=======


# Your WebSocket connection and subscription logic
async def main():
    # url = "wss://wspap.okx.com:8443/ws/v5/private"
    global ws
    url = "wss://ws.okx.com:8443/ws/v5/private"
    ws = WsPrivateAsync(
        # apiKey="cfa32491-8e93-4537-9106-e2a36305a936",
        # passphrase="Trade@1998",
        # secretKey="434E8A9CC1A729DB292C0819AAE8FBAF",
        apiKey = apiKey,
        passphrase=passphrase,
        secretKey=secretKey,
        url=url,
        useServerTime=False
    )
    await ws.start()
    args = []
    # arg1 = {"channel": "account", "ccy": "USDT"}
    # arg1 = {"channel": "balance", "ccy": "USD"}

    # arg2 = {"channel": "orders", "instType": "ANY"}
    # arg3 = {"channel": "balance_and_position"}
    # arg1 = {"channel": "positions","instType":"FUTURES"}
    arg1 = {"channel": "account","ccy":"USDT"}

    
    args.append(arg1)
    # args.append(arg2)
    # args.append(arg3)

    await ws.subscribe(args, callback=emitToclient)
    # await listen_to_websocket()
    # Keep the WebSocket connection alive
    while True:
        await asyncio.sleep(60)  # Adjust the sleep time as necessary
# Your WebSocket connection and subscription logic

async def unsubscribe():
    # url = "wss://wspap.okx.com:8443/ws/v5/private"
    global ws
    url = "wss://ws.okx.com:8443/ws/v5/private"
    ws = WsPrivateAsync(
        apiKey=apiKey,
        passphrase=passphrase,
        secretKey=secretKey,
>>>>>>> 4d917a6 (working flaskTest but need to fix unsubscribe)
        url=url,
        useServerTime=False
    )
    await ws.start()
    args = []

    arg1 = {"channel": "positions","instType":"ANY"}
    arg2 = {"channel": "orders", "instType": "ANY"}
    arg3 = {"channel": "balance_and_position"}
    # arg3 = {"channel": "fills"}
    
    
    args.append(arg1)
    args.append(arg2)
    args.append(arg3)

    await ws.subscribe(args, callback=emitToclient)
    # Keep the WebSocket connection alive
    while True:
        await asyncio.sleep(60)  # Adjust the sleep time as necessary
# Your WebSocket connection and subscription logic

async def unsubscribe():
    global ws
    url = "wss://ws.okx.com:8443/ws/v5/private"
    ws = WsPrivateAsync(
        apiKey=apiKey,
        passphrase=passphrase,
        secretKey=secretKey,
        url=url,
        useServerTime=False
    )
    await ws.start()
    args = []
    arg1 = {"channel": "account", "ccy": "USDT"}
    arg2 = {"channel": "orders", "instType": "ANY"}
    arg3 = {"channel": "balance_and_position"}
    args.append(arg1)
    args.append(arg2)
    # args.append(arg3)

<<<<<<< HEAD
=======
    # await ws.unsubscribe(args, callback=privateCallback)

    # await listen_to_websocket()
>>>>>>> 4d917a6 (working flaskTest but need to fix unsubscribe)
    # Keep the WebSocket connection alive
    while True:
        await asyncio.sleep(60)  # Adjust the sleep time as necessary


# Function to run the async event loop in a separate thread
def run_websocket():
    try:
        global loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        loop.close()  
        
async def disconnect_websocket():
    global ws
    if ws:
        await ws.stop()  # Custom logic to stop your WebSocket instance
        ws = None
    
<<<<<<< HEAD
=======


>>>>>>> 4d917a6 (working flaskTest but need to fix unsubscribe)
@socketio.on('connect')
def start_websocket():

    thread = threading.Thread(target=run_websocket)
    thread.start()
    return jsonify({"status": "WebSocket started"}), 200



@socketio.on('disconnect')
def handle_disconnect():
    global loop
    asyncio.run_coroutine_threadsafe(disconnect_websocket(), loop)
    
    print("Client disconnected")


# Flask route to start WebSocket connection
@app.route('/start_websocket', methods=['GET'])
def start_websocket():
    thread = threading.Thread(target=run_websocket)
    thread.start()
    return jsonify({"status": "WebSocket started"}), 200

# A basic home route
@app.route('/')
def home():
    return "Flask app is running!", 200

# if __name__ == '__main__':
    # Start the Flask app
    # socketio.run(app,host='0.0.0.0')
