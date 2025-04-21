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
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)  # Enable CORS for all origins

config_source = 'okx_live_trade'

apiKey = config[config_source]['apiKey']
secretKey = config[config_source]['secretKey']
passphrase = config[config_source]['passphrase']


import random
def privateCallback(message):
    print("privateCallback", message)

def emitToclient(message):
    json_msg = json.loads(message)
    print(json_msg)
    data_to_client = "Loading ..."
    
    if json_msg.get('arg'):
        channel = json_msg.get('arg',"Loading ...")['channel']
        data_to_client = json_msg.get('data')
        
    else:
        data_to_client = None
    socketio.emit('oms',json.dumps(data_to_client))


ws = None

loop = asyncio.get_event_loop()  
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
    print("SUBSCRIBED")
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

    arg2 = {"channel": "orders", "instType": "ANY"}
    arg3 = {"channel": "balance_and_position"}
    arg1 = {"channel": "positions","instType":"FUTURES"}
    # arg1 = {"channel": "account","ccy":"USDT"}

    
    args.append(arg1)
    # args.append(arg2)
    # args.append(arg3)

    await ws.subscribe(args, callback=emitToclient)
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
    socketio.run(app,host='0.0.0.0',port='9000')

