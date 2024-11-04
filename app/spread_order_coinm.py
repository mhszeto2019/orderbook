import signal
import asyncio
import threading
# from htx.huobi.client.market import MarketClient as HuobiMarketClient
# from htx.huobi.exception.huobi_api_exception import HuobiApiException
# from htx.huobi.model.market import PriceDepthBboEvent
from okx.websocket.WsPublicAsync import WsPublicAsync
import logging
import logging.config
import yaml  # You need to install PyYAML to use this example
import os
import json
import redis
# Define the path to the YAML file
config_path = os.path.join(os.path.dirname(__file__), "../config_folder", "logging.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)

# Create a logger instance
logger = logging.getLogger("my_app")

import websocket
import threading
import time
import json
import gzip
from datetime import datetime
from decimal import Decimal

htx_data = None

class OKXWebSocketClient:
    def __init__(self, url="wss://wspap.okx.com:8443/ws/v5/public"):
        self.url = url
        self.ws = None
        self.args = []
        self.okx_data = None
        
    async def start(self):
        """Start the WebSocket connection."""
        self.ws = WsPublicAsync(url=self.url)
        await self.ws.start()

    async def subscribe(self, channel, inst_id, callback):
        """Subscribe to a specific channel and instrument ID."""
        arg = {"channel": channel, "instId": inst_id}
        self.args.append(arg)
        await self.ws.subscribe(self.args, callback)

    async def run(self, channel, inst_id, callback):
        """Run the WebSocket client, subscribing to the given channel."""
        await self.start()
        await self.subscribe(channel, inst_id, callback)

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
            await self.ws.unsubscribe(self.args, self.publicCallback)

    async def close(self):
        """Close the WebSocket connection."""
        if self.ws:
            await self.ws.close()
            print("WebSocket connection closed.")

    def publicCallback(self,message):
        """Callback function to handle incoming messages."""
        self.okx_data = message
        print("publicCallback", message)


class RedisSubscriber:
    def __init__(self, host='localhost', port=6379, channel='order_updates'):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.channel = channel
        self.redis_data = None  # Store the latest data received

    def start(self):
        """Start the Redis subscriber and listen for messages."""
        self.pubsub.subscribe(**{self.channel: self.handle_message})
        print(f"Subscribed to Redis channel: {self.channel}")
        self.listen()

    def listen(self):
        """Listen for messages on the subscribed channel."""
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                self.handle_message(message)

    def handle_message(self, message):
        """Handle incoming messages from Redis."""
        self.redis_data = json.loads(message['data'])
        print("Received data from Redis:", self.redis_data)

class HTXWebSocketClient:
    def __init__(self, host: str, path: str):
        self._host = host
        self._path = path
        self._active_close = False
        self._has_open = False
        self._sub_str = None
        self._ws = None
        self.htx_data = None

    def open(self):
        url = 'wss://{}{}'.format(self._host, self._path)
        self._ws = websocket.WebSocketApp(url,
                                          on_open=self._on_open,
                                          on_message=self._on_msg,
                                          on_close=self._on_close,
                                          on_error=self._on_error)
        t = threading.Thread(target=self._ws.run_forever, daemon=True)
        t.start()

    def getcurrentdate(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    def _on_open(self, ws):
        print('WebSocket opened:', f'wss://{self._host}{self._path}')
        print("CurrentDatetime:{} GMT+2".format(self.getcurrentdate()))
        self._has_open = True

    def _on_msg(self, ws, message):
        plain = gzip.decompress(message).decode()
        jdata = json.loads(plain)
        if 'ping' in jdata:
            sdata = plain.replace('ping', 'pong')
            self._ws.send(sdata)
        else:
            self.htx_data = jdata  # Update the last received data
            # print("Received WebSocket data:", jdata)

    def _on_close(self, ws):
        print("WebSocket closed.")
        self._has_open = False
        if not self._active_close and self._sub_str is not None:
            self.open()
            self.sub(self._sub_str)

    def _on_error(self, ws, error):
        print("WebSocket error:", error)

    def sub(self, sub_str: dict):
        if not self._has_open:
            time.sleep(1)
        self._sub_str = sub_str
        self._ws.send(json.dumps(sub_str))  # Send subscription request as JSON
        print("Subscribed with:", sub_str)

    def close(self):
        self._active_close = True
        self._sub_str = None
        self._has_open = False
        self._ws.close()


if __name__ == '__main__':
    # Start the Redis subscriber in a separate thread
    redis_subscriber = RedisSubscriber()
    redis_thread = threading.Thread(target=redis_subscriber.start)
    redis_thread.start()

    # Wait for initial data from Redis before starting WebSocket connections
    print("Waiting for data from Redis...")
    while not redis_subscriber.redis_data:
        time.sleep(1)

    # Initialize Huobi and OKX WebSockets after receiving Redis data
    print("Connecting to WebSockets with Redis data.")
    host_huobi = 'api.huobi.pro'
    path_huobi = '/ws'
    host_okx = 'api.okx.com'
    path_okx = '/ws/v5/public'

    huobi_subscriber =HTXWebSocketClient(host_huobi, path_huobi)
    huobi_thread = threading.Thread(target=huobi_subscriber.start)
    huobi_thread.start()
    okx_subscriber = OKXWebSocketClient("wss://wspap.okx.com:8443{}".format(path_okx))
    okx_thread = threading.Thread(target=okx_subscriber.start)
    okx_thread.start()

    huobi_ws = HTXWebSocketClient(host_huobi, path_huobi)
    okx_ws = OKXWebSocketClient("wss://wspap.okx.com:8443{}".format(path_okx))

    huobi_ws.open()

    # Subscribe to channels on both WebSockets based on Redis data
    huobi_sub_params = {'sub': 'market.btcusdt.bbo'}

    huobi_ws.sub(huobi_sub_params)
    okx_ws.run("bbo-tbt", "BTC-USD", okx_ws.publicCallback)

    # Continuously print the latest WebSocket data received
    try:
        while True:
            print('comparison')
            print(huobi_ws.htx_data)

            print(okx_ws.okx_data)
            # if huobi_ws.htx_data:
            #     print("Latest Huobi WebSocket data:", huobi_ws.htx_data)
            # if okx_ws.okx_data:
            #     print("Latest OKX WebSocket data:", okx_ws.okx_data)
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        huobi_ws.close()
        okx_ws.close()
        redis_thread.join()