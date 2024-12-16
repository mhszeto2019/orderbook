from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS  # Import CORS

import asyncio
import websockets
import json
import threading
import datetime
import redis  # Redis for caching
import os
import sys
import hmac
import hashlib
import base64
import configparser
config = configparser.ConfigParser()
util_folder_path = os.path.join(os.path.dirname(__file__), '../')
sys.path.insert(0, util_folder_path)

from util import decoder, unix_ts_to_datetime,standardised_ccy_naming,mapping_for_ccy,format_arr_4dp,format_arr_1dp

config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app, cors_allowed_origins="*")
socketio = SocketIO(app, cors_allowed_origins="*",async_mode='gevent')

CORS(app)  # Enable CORS for all origins

async def okx_websocket():
    url = "wss://ws.okx.com:8443/ws/v5/public"
    async with websockets.connect(url, ping_interval=20, ping_timeout=None) as ws:
        print("Connected " + datetime.datetime.now().isoformat())
        unix_ts = datetime.datetime.now().strftime('%s')
        api_key = config['okx']['api_key']
        secret_key = config['okx']['secret_key']
        passphrase = config['okx']['passphrase']
        message = unix_ts + 'GET' + '/users/self/verify'
        
        # Create HMAC SHA256 signature
        signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
        base64_signature = base64.b64encode(signature).decode('utf-8')
        
        subs = {
            "op": "login",
            "args": [
                {
                    "apiKey": api_key,
                    "passphrase": passphrase,
                    "timestamp": unix_ts,
                    "sign": base64_signature
                }
            ]
        }

        await ws.send(json.dumps(subs))
        
        async for msg in ws:
            msg = json.loads(msg)
            # condition if it is not a login, there will be data in the websocket data
            try: 
                if msg.get('code') == "0":
                    print("Login Success")
                    subs2 = {
                        "op": "subscribe",
                        "args": [
                            {
                                "channel": "books5",
                                "instId": "BTC-USDT"
                            }
                            ,
                            {
                                "channel": "books5",
                                "instId": "BTC-USDC"
                            }
                            ,
                            {
                                "channel": "books5",
                                "instId": "BTC-USDT-SWAP"
                            }
                            ,
                            {
                                "channel": "books5",
                                "instId": "BTC-USDC-SWAP"
                            }
                            ,
                            {
                                "channel": "books5",
                                "instId": "BTC-USD-SWAP"
                            }
                        ]
                    }
                    await ws.send(json.dumps(subs2))

                    async for msg in ws:
                        
                        response_data = json.loads(msg)
                        if 'data' in response_data:
                            bids = response_data['data'][0].get('bids', [])
                            asks = response_data['data'][0].get('asks', [])
                            bids = format_arr_1dp(bids)
                            asks = format_arr_1dp(asks)
                            # print(bids,asks)
                            ccy = standardised_ccy_naming(response_data['data'][0].get('instId',''))
                            if ccy in {"btcusdswap"}:
                                ccy = "coin-m"
                            ts = unix_ts_to_datetime(response_data['data'][0].get('ts',0))
                            data_to_client = {"exchange":"OKX","ccy":ccy, "bids":bids,"asks":asks,"ts":ts}

                            socketio.emit('okx_orderbook', {'data': data_to_client}) 

            except websockets.ConnectionClosed:
                print("Connection closed, exiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
                    # await asyncio.sleep(1)  # Adjust the time delay (in seconds)
    print("Disconnected " + datetime.datetime.now().isoformat())

# Run the WebSocket client in a background thread
def run_okx_client():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(okx_websocket())

@app.route('/')
def index():
    return "OKX WebSocket Flask Server Running"

def handle_shutdown(signal, frame):
    print("Shutting down...")
    socketio.stop()  # Stop socketio
    sys.exit(0)



# SocketIO event to notify frontend when a client connects
@socketio.on('connect')
def handle_connect():
    print("Client connected")
    # Start the WebSocket client using a background task
    socketio.start_background_task(run_okx_client)

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

# import signal
# signal.signal(signal.SIGTERM, handle_shutdown)
if __name__ == '__main__':
    # Run Flask server
    socketio.run(app, host='0.0.0.0', port=5099)
