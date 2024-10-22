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

def privateCallback(message):
    print("privateCallback", message)

def emitToclient(message):
    socketio.emit('hello',json.dumps(message))

config_source = 'okx_test_trade'

api_key = config[config_source]['apiKey']
secret_key = config[config_source]['secretKey']
passphrase = config[config_source]['passphrase']


# Your WebSocket connection and subscription logic
async def main():
    # url = "wss://wspap.okx.com:8443/ws/v5/private"
    url = "wss://ws.okx.com:8443/ws/v5/private"
    ws = WsPrivateAsync(
        apiKey="cfa32491-8e93-4537-9106-e2a36305a936",
        passphrase="Trade@1998",
        secretKey="434E8A9CC1A729DB292C0819AAE8FBAF",
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
    args.append(arg3)

    await ws.subscribe(args, callback=emitToclient)
    
    # Keep the WebSocket connection alive
    while True:
        await asyncio.sleep(60)  # Adjust the sleep time as necessary

# Function to run the async event loop in a separate thread
# def run_websocket():
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(main())



# Function to run the async event loop in a separate thread
def run_websocket():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

@socketio.on('connect')
def start_websocket():
    thread = threading.Thread(target=run_websocket)
    thread.start()
    return jsonify({"status": "WebSocket started"}), 200


@socketio.on('disconnect')
def handle_disconnect():
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

