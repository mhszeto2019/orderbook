from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS  # Import CORS
import asyncio
import websockets
import json
import configparser
import threading
import datetime
import redis  # Redis for caching

import os
import sys
import hmac
import hashlib
import base64

config = configparser.ConfigParser()
util_folder_path = os.path.join(os.path.dirname(__file__), '../')
sys.path.insert(0, util_folder_path)

from util import decoder, unix_ts_to_datetime,standardised_ccy_naming

config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)  # Enable CORS for all origins

async def okx_websocket():
    url = "wss://ws.okx.com:8443/ws/v5/public"
    async with websockets.connect(url, ping_interval=20, ping_timeout=None) as ws:
        print("Connected " + datetime.datetime.now().isoformat())
        unix_ts = datetime.datetime.now().strftime('%s')
        # print(unix_ts)
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
            if msg.get('code') == "0":
                print("Login Success")
                subs2 = {
                    "op": "subscribe",
                    "args": [
                        {
                            "channel": "funding-rate",
                            "instId": "BTC-USDT-SWAP"
                        },
                         {
                            "channel": "funding-rate",
                            "instId": "BTC-USDC-SWAP"
                        },
                        {
                            "channel": "funding-rate",
                            "instId": "BTC-USD-SWAP"
                        }
                    ]
                }
                await ws.send(json.dumps(subs2))

                async for msg in ws:
                    response_data = json.loads(msg)
                    print(response_data)
                    if 'data' in response_data:
                        funding_rate = response_data['data'][0].get('fundingRate', None)
                        fundingTime = unix_ts_to_datetime(response_data['data'][0].get('fundingTime', []))
                        
                        ccy = standardised_ccy_naming(response_data['data'][0].get('instId',''))
                        if ccy in {"btcusdswap"}:
                                ccy = "coin-m"
                        ts = unix_ts_to_datetime(response_data['data'][0].get('ts',0))
                      
                        data_to_client = {"exchange":"OKX","ccy":ccy, "funding_rate": str(round(float(funding_rate) * 100,6))+"% ({})".format(fundingTime),"ts":ts}
                        print(data_to_client)
                        # Emit the received data to the frontend
                        socketio.emit('okx_funding_rate', {'data': json.dumps(data_to_client)}) 

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


@socketio.on('connect')
def handle_connect():
    print("Client connected")
    # Start the WebSocket client using a background task
    socketio.start_background_task(run_okx_client)

if __name__ == '__main__':
    # Run Flask server
    socketio.run(app, host='127.0.0.1', port=5001)
