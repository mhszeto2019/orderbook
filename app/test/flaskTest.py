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
socketio = SocketIO(app)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)  # Enable CORS for all origins
import random
def privateCallback(message):
    print("privateCallback", message)

def emitToclient(message):
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

ws = None

loop = asyncio.get_event_loop()  

# Queue to handle messages (optional, but useful if multiple consumers are needed)
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
        url=url,
        useServerTime=False
    )
    await ws.start()
    args = []
    arg1 = {"channel": "account", "ccy": "BTC"}
    arg2 = {"channel": "orders", "instType": "ANY"}
    arg3 = {"channel": "balance_and_position"}
    args.append(arg1)
    args.append(arg2)
    # args.append(arg3)

    # await ws.unsubscribe(args, callback=privateCallback)

    # await listen_to_websocket()
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

if __name__ == '__main__':
    # Start the Flask app
    # app.run(debug=True, use_reloader=False)
    socketio.run(app)

