import asyncio
from okx.websocket.WsPublicAsync import WsPublicAsync
import redis
import json
from datetime import datetime
import os
import json
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import configparser
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
# Read the configuration file
config.read(config_file_path)
config_source = 'redis'
REDIS_HOST = config[config_source]['host']
REDIS_PORT = config[config_source]['port']
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

from util import get_logger 
logger = get_logger(os.path.basename(__file__))
# SOCKETIO SETUP
from flask_socketio import SocketIO
from flask import Flask
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # Enable CORS for all origins
socketio = SocketIO(app, cors_allowed_origins="*",async_mode='gevent')

class OKXWebSocketClient:
    # wss://ws.okx.com:8443/ws/v5/public
    def __init__(self, url="wss://wspap.okx.com:8443/ws/v5/public"):
        self.url = url
        self.ws = None
        self.subscribed_pairs = []  # To keep track of subscribed pairs
    async def start(self):
        """Start the WebSocket connection."""
        self.ws = WsPublicAsync(url=self.url)
        await self.ws.start()

    async def subscribe(self, channel, inst_id, callback):
        """Subscribe to a specific channel and instrument ID."""
        arg = {"channel": channel, "instId": inst_id}
        self.subscribed_pairs.append(inst_id)  # Track the subscription
        await self.ws.subscribe([arg], callback)  # Subscribe using the args list

    async def run(self, channel,currency_pairs, callback):
        """Run the WebSocket client, subscribing to the given currency pairs."""
        await self.start()
        # Subscribe to all specified currency pairs
        for pair in currency_pairs:
            await self.subscribe(channel, pair, callback)

        # Keep the connection alive
        try:
            while True:
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
        if 'data' in json_data:
            funding_rate = json_data['data'][0].get('fundingRate', None)
            fundingTime = json_data['data'][0].get('fundingTime', [])
            print('ccy',json_data['data'][0].get('instId',''))
            ccy = json_data['data'][0].get('instId','')
            
            ts = int(json_data['data'][0].get('ts',0))/ 1000
            readable_timestamp = datetime.fromtimestamp(ts)

            # Format the timestamp as a human-readable string
            formatted_timestamp = readable_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            print(readable_timestamp)
            data_to_client = {"exchange":"OKX","ccy":ccy, "funding_rate": str(round(float(funding_rate) * 100,6))+"% ({})".format(fundingTime),"ts":formatted_timestamp}
            msg = json.dumps(data_to_client)

            socketio.emit(f'okxfunding_rate/{ccy}',data_to_client)
            print('sending to client',ccy)
            
            
client = None
# Example usage
async def main():
    global client
    client = OKXWebSocketClient()
    # List of currency pairs to subscribe to
    # currency_pairs = ["BTC-USDC", "BTC-USDT","BTC-USD-SWAP"]  # Add more pairs as needed
    currency_pairs = ["BTC-USD-SWAP"]  # Add more pairs as needed
    
    channel = 'funding-rate'
    await client.run(channel,currency_pairs, client.publicCallback)

loop = None

def run_okx_client():
    print('running_okx_client')
    global loop    
    try:
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except Exception as e:
        loop.close()

@socketio.on('connect')
def handle_connect(auth):
    print('handleconnectmsg',auth)
    global loop
    # if loop != None:
    #     loop.close()
    print("Client connected")
    # Start the WebSocket client using a background task
    socketio.start_background_task(run_okx_client)

# @socketio.on('disconnect')
# def handle_disconnect():
#     global loop
#     print("Client disconnected")
#     loop.close()

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
    print("Client disconnected")
    if loop and loop.is_running():
        # Stop all running tasks
        for task in asyncio.all_tasks(loop):
            task.cancel()
        # Optionally stop the event loop (not close)
        loop.call_soon_threadsafe(loop.stop)


@socketio.on('message')
def handle_message(data):
    print('Received message: ' + str(data))
    # Echo the message back
    socketio.send(data)


# Running the Flask application with Gevent Worker
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=6040, use_reloader=False)