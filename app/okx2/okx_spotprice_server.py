
from flask import Flask,request
from flask_socketio import SocketIO, emit
import asyncio
import websockets
import json
import configparser
import threading
import datetime
import redis  # Redis for caching
from flask_cors import CORS  # Import CORS
import os
import sys
import hmac
import hashlib
import base64
import gevent.monkey
import logging

logging.basicConfig(level=logging.DEBUG)
gevent.monkey.patch_all()
config = configparser.ConfigParser()
util_folder_path = os.path.join(os.path.dirname(__file__), '../')
sys.path.insert(0, util_folder_path)

from util import decoder, unix_ts_to_datetime,standardised_ccy_naming,mapping_for_ccy

config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app, cors_allowed_origins="*") 
socketio = SocketIO(app, cors_allowed_origins="*",async_mode='gevent')
CORS(app)  # Enable CORS for all origins

# Connect to Redis server
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Store data in Redis with a TTL (e.g., 100 seconds)
def cache_data(key, data, ttl=100):
    redis_client.set(key, json.dumps(data), ex=ttl)

# Retrieve data from Redis
def get_cached_data(key):
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None

async def okx_websocket():
    url = "wss://ws.okx.com:8443/ws/v5/public"

    async with websockets.connect(url, ping_interval=None, ping_timeout=None) as ws:
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
            if msg.get('code') == "0":
                try:
                    print("Login Success")
                                        
                    
                    # Unsubscribe from all channels first
                    unsubscribe = {
                        "op": "unsubscribe",
                        
                    }
                    await ws.send(json.dumps(unsubscribe))
                    print("Unsubscribed from channels")

                    subs2 = {
                        "op": "subscribe",
                        "args": 
                            [
                                {
                                "channel": "tickers",
                                "instId": "BTC-USDT"
                                }
                                ,
                                {
                                "channel": "tickers",
                                "instId": "BTC-USDC"
                                },
                                {
                                "channel": "tickers",
                                "instId": "BTC-USDT-SWAP"
                                },
                                {
                                "channel": "tickers",
                                "instId": "BTC-USDC-SWAP"
                                },
                                {
                                "channel": "tickers",
                                "instId": "BTC-USD-SWAP"
                                }
                            ]
            
                    }
                    await ws.send(json.dumps(subs2))

                    async for msg in ws:
                        # parse json string to python dictionary
                        response_data = json.loads(msg)
                        if 'data' in response_data:
                            ccy = standardised_ccy_naming(response_data['data'][0].get('instId', []))
                            if ccy in {"btcusdswap"}:
                                ccy = "coin-m"

                            lastPrice = response_data['data'][0].get('last', [])
                            lastSize = response_data['data'][0].get('lastSz', [])
                            bidPrice = response_data['data'][0].get('bidPx', [])
                            bidSize = response_data['data'][0].get('bidSz', [])
                            askPrice = response_data['data'][0].get('askPx', [])
                            askSize = response_data['data'][0].get('askSz', [])
                            
                            ts = unix_ts_to_datetime(response_data['data'][0].get('ts',0))
                            channel = url,response_data['arg'].get('channel','None')
                            
                            data_to_client = dict({"exchange":"OKX",
                                                   "ccy": ccy, 
                                                   "lastPrice": lastPrice, 
                                                   "lastSize": lastSize, 
                                                   "ts": ts,
                                                   "channel":channel,
                                                   "bidPrice":bidPrice,
                                                   "bidSize":bidSize,
                                                   "askPrice":askPrice,
                                                   "askSize":askSize
                                                   })
                            try:
                                socketio.emit('okx_live_price_{}'.format(ccy), {'data': json.dumps(data_to_client)})
                                
                            except Exception as e:
                                print(f"Error emitting data for {ccy}: {str(e)}")
                            # Cache the received data into Redis
                            cache_data('okx_live_price_{}'.format(ccy), data_to_client)

                        # await asyncio.sleep(1)  # Adjust the time delay (in seconds)
                except Exception as e:
                    print("ERRROR",e)
    
                except websockets.ConnectionClosed:
                    print("WebSocket connection closed")
                except Exception as e:
                    print(f"Error in WebSocket communication: {e}")

    print("Disconnected " + datetime.datetime.now().isoformat())

# Run the WebSocket client in a background thread
def run_okx_client():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(okx_websocket()) 

@app.route('/')
def index():
    return "OKX WebSocket price Flask Server Running"

@app.route('/get_redis_data')
def get_redis_data():
    ccy = request.args.get('ccy')
    request_info = f'okx_live_price_{ccy}'
    print(request_info)
    data = get_cached_data(request_info)
    print(data)
    return {"data":data}

def handle_shutdown(signal, frame):
    print("Shutting down...")
    socketio.stop()  # Stop socketio
    sys.exit(0)



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
    # Start WebSocket client in a background thread
    # threading.Thread(target=run_okx_client).start()
    # Run Flask server
    socketio.run(app, host='0.0.0.0', port=5002)
