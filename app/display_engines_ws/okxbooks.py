import asyncio
from okx.websocket.WsPublicAsync import WsPublicAsync
import redis
import json
from datetime import datetime
import os
import json
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.util import unix_ts_to_datetime
import configparser
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
# Read the configuration file
config.read(config_file_path)
config_source = 'redis'
REDIS_HOST = config[config_source]['host']
REDIS_PORT = config[config_source]['port']
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


# SOCKETIO SETUP
from flask_socketio import SocketIO
from flask import Flask
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # Enable CORS for all origins
socketio = SocketIO(app, cors_allowed_origins="*",async_mode='gevent')

# Set log directory and filename
LOG_DIR = '/var/www/html/orderbook/logs'
log_filename = os.path.join(LOG_DIR, 'orderbooks_okx_data.log')
os.makedirs(LOG_DIR, exist_ok=True)

# Set up basic logging configuration
# Logger 
from pathlib import Path
# Define the log directory and the log file name
LOG_DIR = Path('/var/www/html/orderbook/logs')
log_filename = LOG_DIR / (Path(__file__).stem + '.log')
os.makedirs(LOG_DIR, exist_ok=True)
# Set up basic logging configuration
import logging
file_handler = logging.FileHandler(log_filename)
# Set up a basic formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger = logging.getLogger('okxbooks')
logger.setLevel(logging.DEBUG)  # Set log level
# Add the file handler to the logger
logger.addHandler(file_handler)
import traceback

class OKXWebSocketClient:
    def __init__(self, url="wss://ws.okx.com:8443/ws/v5/public"):
        self.url = url
        self.ws = None
        self.subscribed_pairs = []  # To keep track of subscribed pairs
        self.is_client_running = False

    async def start(self):
        """Start the WebSocket connection."""
        self.ws = WsPublicAsync(url=self.url)
        await self.ws.start()

    async def subscribe(self, channel, inst_id, callback):
        try:
            """Subscribe to a specific channel and instrument ID."""
            arg = {"channel": channel, "instId": inst_id}
            self.subscribed_pairs.append(inst_id)  # Track the subscription
            await self.ws.subscribe([arg], callback)  # Subscribe using the args list
        except Exception as e:
            logger.error(f"okxbooks subscription error:{traceback.format_exc()}")

    async def run(self, channel,currency_pairs, callback):
        try:
            """Run the WebSocket client, subscribing to the given currency pairs."""
            await self.start()
            # Subscribe to all specified currency pairs
            for pair in currency_pairs:
                await self.subscribe(channel, pair, callback)

        # Keep the connection alive
            while self.is_client_running:
                await asyncio.sleep(1)  # Keep the event loop running
            
        except KeyboardInterrupt:
            print("Disconnecting...")
            await self.unsubscribe()  # Unsubscribe when exiting
        finally:

            await self.close()  # Ensure WebSocket is closed when done
    
    async def unsubscribe(self):
        """Unsubscribe from all channels."""
        if self.ws:
            print("Unsubscribing from all channels...")
            await self.ws.unsubscribe(self.subscribed_pairs)

    async def close(self):
        """Close the WebSocket connection."""
        if self.ws:
            await self.ws.factory.close()
            print("WebSocket connection closed.")
        redis_client.close()

    @staticmethod
    def publicCallback(message):
        """Callback function to handle incoming messages."""
        json_data = json.loads(message)
        if json_data.get('data'):
            channel = json_data["arg"]["channel"]
            currency_pair = json_data["arg"]["instId"]
            instrument = 'SPOT'
            # Extract bids and asks
            # ask_list = [{"price": str(price), "size": str(size)} for price, size in asks][::-1]
            bid_list = [{"price": bid[0], "size": bid[1]} for bid in json_data["data"][0]["bids"]]
            ask_list = [{"price": ask[0], "size": ask[1]} for ask in json_data["data"][0]["asks"]][::-1]
            bid_list_json = json.dumps(bid_list)
            ask_list_json = json.dumps(ask_list)
            
            # Prepare a dictionary of the fields to store
            redis_data = {
                "currency": currency_pair,
                "channel": channel,
                "bid_list":bid_list_json,
                "ask_list":ask_list_json,
                "ask_price": json_data["data"][0]["asks"][0][0],  # Renamed for consistency
                "ask_size": json_data["data"][0]["asks"][0][1],   # Renamed for consistency
                "bid_price": json_data["data"][0]["bids"][0][0],  # Renamed for consistency
                "bid_size": json_data["data"][0]["bids"][0][1],   # Renamed for consistency
                "timestamp": datetime.fromtimestamp(float(json_data["data"][0]["ts"]) / 1000).strftime('%Y-%m-%d %H:%M:%S.%f'),
                "sequence_id": json_data["data"][0]["seqId"],
                "exchange":"okx"
            }
            
            try:
                socketio.emit(currency_pair,redis_data)
                logger.info(redis_data)
            except Exception as e:
                logger.debug(f"ERROR EMITTING TO CLIENT {e}")
            # logger.info(redis_data['timestamp'])
            # print('sending to client')
            if 'SWAP' in currency_pair:
                instrument = 'SWAP'
            
client = None
loop = None
from threading import Thread
from gevent import monkey 

# Example usage
async def main():
    global client
    client = OKXWebSocketClient()
    client.is_client_running = True
    print(client.is_client_running)
    # List of currency pairs to subscribe to
    # currency_pairs = ["BTC-USDC", "BTC-USDT","BTC-USD-SWAP"]  # Add more pairs as needed
    currency_pairs = ["BTC-USD-SWAP"]  # Add more pairs as needed
    channel = 'books5'
    await client.run(channel,currency_pairs, client.publicCallback)


def run_okx_client():
    print('running_okx_client')
    global loop    
    try:
        if loop!= None:
            loop.close()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except Exception as e:
        print('closing loop in run_okx_client')
        loop.stop()

@socketio.on('connect')
def handle_connect(auth):
    global loop
    monkey.patch_all()
    # if loop != None:
    #     loop.close()
    print("Client connected")
    # Start the WebSocket client using a background task
    socketio.start_background_task(run_okx_client)

@socketio.on('client_change')
def handle_client_change(data):
    global loop
   
    print(f"Client change detected with data: {data}")
    if loop is not None:
        try:
            loop.run_until_complete(client.cleanup())
            print("Client WebSocket connection cleaned up.")
        except Exception as e:
            print(f"Error during client change cleanup: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    global loop
    print('loop in disconnect',loop)
    # loop.run_until_complete(client.unsubscribe())x

    print("Client disconnected")
    if loop and loop.is_running():
        # Stop all running tasks
        for task in asyncio.all_tasks(loop):
            task.cancel()
        # Optionally stop the event loop (not close)
        loop.call_soon_threadsafe(loop.stop)


@socketio.on('message')
def handle_message(data):
    # print('Received message: ' + str(data))
    # Echo the message back
    socketio.send(data)


# Running the Flask application with Gevent Worker
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5090, use_reloader=False)