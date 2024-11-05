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
    def __init__(self,subscribed_channel, host='localhost', port=6379):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.subscribed_channel = subscribed_channel
        self.redis_data = {} 

    def start(self):
        """Start the Redis subscriber."""
        print(self.subscribed_channel)

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

orderupdates_redis_subscriber = RedisSubscriber('order_updates')
okxbbo_redis_subscriber = RedisSubscriber('okxbbo_channel')
htxbbo_redis_subscriber = RedisSubscriber('htxbbo_channel')



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


def runokxsubscriber():
    okxbbo_redis_subscriber.start()

def runhtxsubscriber():
    htxbbo_redis_subscriber.start()

def runorderupdatessubscriber():
    orderupdates_redis_subscriber.start()

# Start the event loop for Huobi in a thread
if __name__ == '__main__':
    okx_redis_thread = threading.Thread(target=runokxsubscriber)
    okx_redis_thread.start()

    # Start the Redis subscriber in a separate thread
    orderupdate_redis_thread = threading.Thread(target=runorderupdatessubscriber)
    orderupdate_redis_thread.start()

    # Start the HTTX WebSocket client in the main thread
    asyncio.run(runhtxsubscriber())

    # Wait for the Huobi thread to finish (this may block indefinitely)
    okx_redis_thread.join()
    orderupdate_redis_thread.join()
