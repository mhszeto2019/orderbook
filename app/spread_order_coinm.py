import signal
import asyncio
import threading
from htx.huobi.client.market import MarketClient as HuobiMarketClient
from htx.huobi.exception.huobi_api_exception import HuobiApiException
from htx.huobi.model.market import PriceDepthBboEvent
from okx.websocket.WsPublicAsync import WsPublicAsync
import logging
import logging.config
import yaml  # You need to install PyYAML to use this example
import os
import json
import redis
# Define the path to the YAML file
config_path = os.path.join(os.path.dirname(__file__), "../config_folder", "logging.yaml")
print(config_path)
with open(config_path, "r") as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)

# Create a logger instance
logger = logging.getLogger("my_app")

class RedisSubscriber:
    def __init__(self, host='localhost', port=6379):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.subscribed_channel = 'order_updates'
        self.redis_data = None 

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

import datetime
import websocket
import gzip
import time
class WsBase:
    def __init__(self, host: str, path: str):
        self._host = host
        self._path = path
        self._active_close = False
        self._has_open = False
        self._sub_str = None
        self._ws = None
        self.all_data = []
       

    def get_data(self):
        return self.all_data 

    def open(self):
        url = f'wss://{self._host}{self._path}'
        self._ws = websocket.WebSocketApp(url,
                                          on_open=self._on_open,
                                          on_message=self._on_msg,
                                          on_close=self._on_close,
                                          on_error=self._on_error)
        threading.Thread(target=self._ws.run_forever, daemon=True).start()

    def get_current_date(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    def _on_open(self, ws):
        self._has_open = True

    def _on_msg(self, ws, message):
        plain = gzip.decompress(message).decode()
        response_data = json.loads(plain)
        self.handle_ping(response_data, plain)

        current_date = self.get_current_date()
        self.all_data.append({"timestamp": current_date, "data": response_data})

        if 'ch' in response_data and 'tick' in response_data:
            self.process_tick_data(response_data)

    def handle_ping(self, response_data, plain):
        if 'ping' in response_data or response_data.get('op') == 'ping' or response_data.get('action') == 'ping':
            # print("ping: " + plain)
            sdata = plain.replace('ping', 'pong')
            self._ws.send(sdata)
            # print("pong: " + sdata)

    def process_tick_data(self, response_data):
        # To be implemented in subclasses
        pass

    def _on_close(self, ws, close_status_code, close_msg):
        print(f"WebSocket closed: {close_status_code} - {close_msg}")
        self._has_open = False
        self.reconnect()

    def reconnect(self):
        retry_count = 0
        max_retries = 5
        retry_delay = 5  # seconds

        while not self._active_close and retry_count < max_retries:
            try:
                print(f"Reconnecting... Attempt {retry_count + 1}")
                time.sleep(retry_delay)
                self.open()
                if self._sub_str is not None:
                    self.sub(self._sub_str)
                break  # Break if reconnection is successful
            except Exception as e:
                print(f"Reconnection failed: {e}")
                retry_count += 1
                retry_delay *= 2  # Exponential backoff

        if retry_count == max_retries:
            print("Max reconnection attempts reached. Giving up.")   

    def _on_error(self, ws, error):
        print(error)

    def sub(self, sub_str: dict):
        if self._active_close:
            print('Already closed')
            return
        while not self._has_open:
            time.sleep(1)

        self._sub_str = sub_str
        self._ws.send(json.dumps(sub_str))  # Send as JSON string
        print('sub_str', sub_str)

    def req(self, req_str: dict):
        if self._active_close:
            print('Already closed')
            return
        while not self._has_open:
            time.sleep(1)

        self._ws.send(json.dumps(req_str))  # Send as JSON string
        print(req_str)

    def close(self):
        self._active_close = True
        self._sub_str = None
        self._has_open = False
        self._ws.close()

class Ws_orderbook(WsBase):
    def __init__(self, host: str, path: str):
        super().__init__(host, path)
        self._ws = None
        self.bids= None
        self.asks= None
        self.ts = None

    def process_tick_data(self, response_data):
        self.bids = response_data['tick'].get('bids', [])
        self.asks = response_data['tick'].get('asks', [])
        self.ts = self.unix_ts_to_datetime(response_data['ts'])


    @staticmethod
    def unix_ts_to_datetime(ts):
        # Convert Unix timestamp to datetime
        return datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M:%S')
    
# Instantiate Huobi client
# huobi_client = HuobiMarketClient()
huobi_client = Ws_orderbook("api.hbdm.com",'/swap-ws')
okx_client = OKXWebSocketClient()
redis_subscriber = RedisSubscriber()

huobi_data = None  # Store the last received Huobi data
from decimal import Decimal
# Comparison logic
def compare_prices(huobi_data, okx_data):
    """Compare prices from Huobi and OKX."""
    # Check if we have valid data from both brokers
    # print(huobi_data,type(huobi_data),okx_data,type(okx_data))
    if huobi_data and okx_data:
        
        huobi_ask,huobi_bid = Decimal(huobi_data[1]),Decimal(huobi_data[3]) # Adjust based on actual data structure
        okx_ask,okx_askSz,okx_bid,okx_bidSz = Decimal(okx_data['data'][0]['asks'][0][0]),Decimal(okx_data['data'][0]['asks'][0][1]),Decimal(okx_data['data'][0]['bids'][0][0]),Decimal(okx_data['data'][0]['bids'][0][1])  # Adjust for OKX data structure
        redis_dict = redis_subscriber.redis_data
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
            print('hee')
# Callback for Huobi
def huobi_callback(price_depth_event: PriceDepthBboEvent):
    """Handle the price depth event from Huobi."""
    global huobi_data
    print("Huobi Data:")
    # price_depth_event.print_object()
    # price_depth_event = dict({"ask":price_depth_event.tick.ask,"askSz":price_depth_event.tick.askSize,"bid":price_depth_event.tick.bid,"bid"})
    price_depth_event = [price_depth_event.tick.symbol,price_depth_event.tick.ask,price_depth_event.tick.askSize,price_depth_event.tick.bid,price_depth_event.tick.bidSize,price_depth_event.tick.quoteTime]

    huobi_data = price_depth_event  # Store the latest Huobi data
    compare_prices(huobi_data, json.loads(okx_client.okx_data))  # Compare with OKX data

# Error handling for Huobi
def huobi_error(e: HuobiApiException):
    print(f"Huobi Error: {e.error_code} {e.error_message}")

# Start OKX WebSocket Client
async def run_okx_client():
    await okx_client.run("bbo-tbt", "BTC-USD-SWAP", okx_client.publicCallback)

def run_huobi_client():
    """Start the Huobi client subscription."""
    huobi_client.sub({"sub":"market.BTC-USD.depth.step0","id":"id5"})

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
