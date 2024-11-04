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

class RedisSubscriber:
    def __init__(self, host='localhost', port=6379):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.subscribed_channel = 'order_updates'
        self.redis_data = {} 

    def start(self):
        """Start the Redis subscriber."""
        self.pubsub.subscribe(**{self.subscribed_channel: self.handle_message})
        print(f"Subscribed to Redis channel: {self.subscribed_channel}")

        # Listen for messages
        self.listen()

    def listen(self):
        """Listen for messages on the subscribed channel."""
        try:
            for message in self.pubsub.listen():
                if message['type'] == 'message':
                    self.handle_message(message)
        except Exception as e:
            print(f"Error while listening to Redis: {e}")

    def handle_message(self, message):
        """Handle incoming messages from Redis."""
        order_data = json.loads(message['data'])
        self.redis_data = order_data
        print("Received order update from Redis:", order_data)

class OKXWebSocketClient:
    def __init__(self, url="wss://wspap.okx.com:8443/ws/v5/public"):
        self.url = url
        self.ws = None
        self.args = []
        self.okx_data = None  # Store the last received data here

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
            await self.ws.unsubscribe(self.args, OKXWebSocketClient.publicCallback)

    async def close(self):
        """Close the WebSocket connection."""
        if self.ws:
            await self.ws.close()
            print("WebSocket connection closed.")

    def publicCallback(self, message):
        """Callback function to handle incoming messages."""
        # print("OKX publicCallback", message)
        # {"arg":{"channel":"bbo-tbt","instId":"BTC-USDT"},"data":[{"asks":[["74165.9","0.00001198","0","1"]],"bids":[["74037.2","4.22723227","0","4"]],"ts":"1730367981772","seqId":26213414}]}
        self.okx_data = message  # Store the incoming data for later comparison

class Ws_orderbook_swaps:
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
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        return current_date

    def _on_open(self, _ws):
        print('ws open')
        print("WssHostAndPath: ", 'wss://{}{}'.format(self._host, self._path))
        current_date = self.getcurrentdate()
        print("CurrentDatetime:{} GMT+2".format(current_date))
        self._has_open = True

    def _on_msg(self, _ws, message):
        # print(message)
        plain = gzip.decompress(message).decode()
        jdata = json.loads(plain)
        if 'ping' in jdata:
            print("ping: " + plain)
            sdata = plain.replace('ping', 'pong')
            self._ws.send(sdata)
            print("pong: " + sdata)
            return
        elif 'op' in jdata:
            opdata = jdata['op']
            if opdata == 'ping':
                sdata = plain.replace('ping', 'pong')
                # print("pong: " + sdata)
                self._ws.send(sdata)
                return
            else:
                pass
        elif 'action' in jdata:
            opdata = jdata['action']
            if opdata == 'ping':
                sdata = plain.replace('ping', 'pong')
                # print("pong: "+ sdata)
                self._ws.send(sdata)
                return
            else:
                pass
        else:
            pass
        current_date = self.getcurrentdate()
        # print("CurrentDatetime:{} GMT+2".format(current_date))
        # print(json.dumps(jdata, indent=4, ensure_ascii=False))
        # print("*************************************")
        # print(jdata)
        # print(type(jdata),jdata)
        compare_prices(jdata, json.loads(okx_client.okx_data)) 
        # Process and store the incoming data
       
        self.htx_data = jdata
    def _on_close(self, _ws):
        print("ws close.")
        self._has_open = False
        if not self._active_close and self._sub_str is not None:
            self.open()
            self.sub(self._sub_str)

    def _on_error(self, _ws, error):
        print(error)

    def sub(self, sub_str: dict):
        if self._active_close:
            print('has close')
            return
        while not self._has_open:
            time.sleep(1)

        self._sub_str = sub_str
        self._ws.send(json.dumps(sub_str))  # as json string to be send
        # print(sub_str)

    def req(self, req_str: dict):
        if self._active_close:
            print('has close')
            return
        while not self._has_open:
            time.sleep(1)

        self._ws.send(json.dumps(req_str))  # as json string to be send
        # print(req_str)

    def close(self):
        self._active_close = True
        self._sub_str = None
        self._has_open = False
        self._ws.close()

class HTXWebSocketClient:
    def __init__(self, url, path):
        self.url = url
        self.ws = None
        self.args = []
        # self.htx_data = None  # Store the last received data here
        self.path = path
        self.htx_data = None
    def start(self):
        """Start the WebSocket connection."""
        # Initialize the WebSocket connection object here
        self.ws = Ws_orderbook_swaps(host=self.url, path=self.path)
        self.ws.open()  # Open the WebSocket connection

    async def subscribe(self, channel, inst_id, callback):
        """Subscribe to a specific channel and instrument ID."""
        if self.ws is None:
            raise ValueError("WebSocket connection is not initialized.")
            
        # Prepare the subscription argument
        arg = {"sub": f"market.{inst_id}.{channel}", "id": "id5"}
        print("Subscribing with argument:", arg)
        
        # Send the subscription request to the WebSocket connection
        self.ws.sub(arg)  # This is a synchronous call, so no need for await

    async def run(self, channel, inst_id, callback):
        """Run the WebSocket client, subscribing to the given channel."""
        # Start the connection before subscribing
        self.start()  # Initializes and opens the WebSocket
        await self.subscribe(channel, inst_id, callback)  # Subscribes to the channel

    async def publicCallback(self):
        """Callback function to handle incoming messages."""
        print(self.ws.htx_data)
        self.htx_data = self.ws.htx_data
        # print(self.okx_data)
        return self.ws.htx_data
         # Store the incoming data for later comparison

# Instantiate Huobi client


huobi_client = HTXWebSocketClient("api.hbdm.com",'/swap-ws')
okx_client = OKXWebSocketClient()
redis_subscriber = RedisSubscriber()

huobi_data = None  # Store the last received Huobi data
# Comparison logic
def compare_prices(huobi_data, okx_data):
    """Compare prices from Huobi and OKX."""
    # Check if we have valid data from both brokers
    # print(huobi_data,type(huobi_data),okx_data,type(okx_data))
    if huobi_data.get('tick') and okx_data:
        
        huobi_ask,huobi_askSz,huobi_bid,huobi_bidDz = Decimal(huobi_data['tick']['ask'][0]),Decimal(huobi_data['tick']['ask'][1]),Decimal(huobi_data['tick']['bid'][0]),Decimal(huobi_data['tick']['bid'][1])  # Adjust based on actual data structure
        okx_ask,okx_askSz,okx_bid,okx_bidSz = Decimal(okx_data['data'][0]['asks'][0][0]),Decimal(okx_data['data'][0]['asks'][0][1]),Decimal(okx_data['data'][0]['bids'][0][0]),Decimal(okx_data['data'][0]['bids'][0][1])  # Adjust for OKX data structure
        redis_dict = redis_subscriber.redis_data

        redis_leading_exchange = redis_dict['leadingExchange']
        redis_lagging_exchange = redis_dict['laggingExchange']
        redis_spread = redis_dict['spread']
        redis_direction = redis_dict['direction']
        redis_qty = redis_dict['qty']
        # print(huobi_ask,huobi_bid,okx_ask,okx_askSz,okx_bid,okx_bidSz)
        # print(Decimal(huobi_ask),Decimal(okx_bid))
        # print(redis_subscriber.redis_data)

        epsilon = 1e-5
        print(huobi_ask,'-',huobi_bid,'-',okx_ask,'-',okx_bid)

        if abs(huobi_ask - okx_bid) < epsilon:
            print("Prices are the same, hold.")
        elif huobi_ask < okx_bid:
            print("Huobi is cheaper, consider buying on HTX and sell on OKX.")
        elif huobi_bid > okx_ask:
            print("OKX is cheaper, consider buying on OKX and sell on HTX.")
        else:
            # print(huobi_ask,'-',huobi_bid,'-',okx_ask,'-',okx_bid)
            # logger.info(huobi_ask,'-',huobi_bid,'-',okx_ask,'-',okx_bid)
            logger.info(f"{huobi_ask} - {huobi_bid} - {okx_ask} - {okx_bid} - {redis_subscriber.redis_data}")

            
# Callback for Huobi
def huobi_callback(price_depth_event):
    """Handle the price depth event from Huobi."""
    global huobi_data,htx_data
    print("Huobi Data:")
    print(price_depth_event)
    # price_depth_event.print_object()
    # price_depth_event = dict({"ask":price_depth_event.tick.ask,"askSz":price_depth_event.tick.askSize,"bid":price_depth_event.tick.bid,"bid"})
    # price_depth_event = [price_depth_event.tick.symbol,price_depth_event.tick.ask,price_depth_event.tick.askSize,price_depth_event.tick.bid,price_depth_event.tick.bidSize,price_depth_event.tick.quoteTime]

    huobi_data = price_depth_event  # Store the latest Huobi data
    # compare_prices(huobi_data, json.loads(okx_client.okx_data))  # Compare with OKX data


# Start OKX WebSocket Client
async def run_okx_client():
    await okx_client.run("bbo-tbt", "BTC-USD", okx_client.publicCallback)


def run_huobi_client():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(huobi_client.run("bbo", "BTC-USD", huobi_callback(huobi_client.htx_data)))
    loop.close()

def run_redis_subscriber():
    redis_subscriber.start()

# Function to handle shutdown
def shutdown_handler(signum, frame):
    print("Shutting down gracefully...")
    # Unsubscribe from all WebSocket streams
    asyncio.run(huobi_client.unsubscribe_all())
    asyncio.run(OKXWebSocketClient.unsubscribe())
    exit(0)

def shutdown_handler(signum, frame):
    print("Shutting down gracefully...")
    exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)



# Start the event loop for Huobi in a thread
if __name__ == '__main__':
    huobi_thread = threading.Thread(target=run_huobi_client)
    huobi_thread.start()

    # Start the Redis subscriber in a separate thread
    redis_thread = threading.Thread(target=run_redis_subscriber)
    redis_thread.start()

    # Start the OKX WebSocket client in the main thread
    asyncio.run(run_okx_client())

    # Wait for the Huobi thread to finish (this may block indefinitely)
    huobi_thread.join()
    redis_thread.join()
