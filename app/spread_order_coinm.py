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
import requests
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
        # print(f"Subscribed to Redis channel: {self.subscribed_channel}")

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
        # print("Received order update from Redis:", order_data)

class MatchingEngine:
    def __init__(self, orderupdates_subscriber, htxbbo_subscriber,okxbbo_subscriber):
        self.orderupdates_subscriber = orderupdates_subscriber
        self.htxbbo_subscriber = htxbbo_subscriber
        self.okxbbo_subscriber = okxbbo_subscriber

    def start(self):
        """Start the matching process."""
        while True:
            self.check_for_matches()
            time.sleep(1)  # Adjust the frequency of checking

    def check_for_matches(self):
        """Check for matches between user criteria and trading data."""
        # print("Order DATA",self.orderupdates_subscriber.redis_data)
        # print("HTX DATA",self.htxbbo_subscriber.redis_data)
        # print("OKX DATA",self.okxbbo_subscriber.redis_data)
        order_data = self.orderupdates_subscriber.redis_data
        huobi_data = self.htxbbo_subscriber.redis_data
        okx_data = self.okxbbo_subscriber.redis_data

        
        if huobi_data and okx_data and order_data:
            okx_bidprice,okx_bidsize, okx_askprice,okx_asksize = Decimal(okx_data['bid_price']),Decimal(okx_data['bid_size']),Decimal(okx_data['ask_price']),Decimal(okx_data['ask_size'])
            htx_bidprice,htx_bidsize, htx_askprice,htx_asksize = Decimal(huobi_data['bid_price']),Decimal(huobi_data['bid_size']),Decimal(huobi_data['ask_price']),Decimal(huobi_data['ask_size'])
            # order_qty,order_spread,order_direction = Decimal(order_data['qty']),Decimal(order_data['spread']),order_data['direction']
            order_currency,order_direction,order_laggingexchange,order_leadingexchange, order_type,order_price,order_qty,order_spread =order_data['currency'],order_data['direction'],order_data['laggingExchange'],order_data['leadingExchange'],order_data['orderType'],Decimal(order_data['price']),Decimal(order_data['qty']),Decimal(order_data['spread'])
            # print(order_currency,order_direction,order_laggingexchange,order_leadingexchange, order_type,order_price,order_qty,order_spread)
            data = {
                "okx_bid": float(okx_bidprice),
                "okx_ask": float(okx_askprice),
                "htx_bid": float(htx_bidprice),
                "htx_ask": float(htx_askprice),
                "okx_bid_size": float(okx_bidsize),
                "okx_ask_size": float(okx_asksize),
                "htx_bid_size": float(htx_bidsize),
                "htx_ask_size": float(htx_bidsize),
                "to_buy": float(htx_bidprice - okx_askprice),
                "to_sell": float(okx_bidprice - htx_askprice),
                "order_qty":float(order_qty),
                "order_spread":float(order_spread),
                "order_direction":order_direction,
                "laggingexh" :order_data['laggingExchange'],
                "order_type":order_type

            }

            json_data = json.dumps(data, indent=4)
            print(json_data)
            
            if order_type == 'limit':
                if order_data['laggingExchange'] == 'htx':
                    if order_data['direction'] == 'buy':
                        if (htx_bidprice - okx_askprice >= order_spread) and okx_asksize >= order_qty and htx_bidsize >= order_qty and okx_bidprice == order_data['price']:
                            print("BUY ON OKX, SELL TO HTX")
                    elif order_data['direction'] == 'sell':
                        # sell to okx 
                        if (htx_askprice - okx_bidprice >= order_spread) and okx_bidprice >= order_qty and  htx_askprice >= order_qty and okx_bidprice == order_data['price']:
                            print("SELL TO OKX, BUY ON HTX")
            elif order_type == 'market':
                if order_data['laggingExchange'] == 'htx':
                    if order_data['direction'] == 'buy':
                        if (htx_bidprice - okx_askprice >= order_spread) and okx_asksize >= order_qty and htx_bidsize >= order_qty:
                            # print("BUY ON OKX, SELL TO HTX")
                            self.execute_trade('hello')
                    elif order_data['direction'] == 'sell':
                        # sell to okx 
                        if (htx_askprice - okx_bidprice >= order_spread) and okx_bidprice >= order_qty and  htx_askprice >= order_qty :
                            print("SELL TO OKX, BUY ON HTX")

            # print(okx_bidprice,okx_askprice,htx_bidprice,htx_askprice,"to buy:",htx_bidprice- okx_askprice , "to sell",okx_bidprice - htx_askprice)
            # print(huobi_ask)
        # # Example of matching logic
        # if user_criteria and trading_data:
        #     if trading_data['symbol'] == user_criteria.get('symbol') and trading_data['price'] <= user_criteria.get('price'):
        #         print("Match found! Executing trade...")
                # self.execute_trade(trading_data)

        # MATCHING CONDITIONS SPECIFIED HERE
        if  self.orderupdates_subscriber.redis_data.get('leadingExchange') == 0:
            self.execute_trade('hello')
            

    def execute_trade(self, trade_data):
        """Execute trade based on matched data."""
        # Integrate with the trading execution system here
        print("TRADE EXECUTING")
        self.orderupdates_subscriber.redis_data = {}
        print(f"Trade executed for: {trade_data}")





orderupdates_redis_subscriber = RedisSubscriber(subscribed_channel='order_updates')
okxbbo_redis_subscriber = RedisSubscriber('okxbbo:btcusdt')
htxbbo_redis_subscriber = RedisSubscriber('htxbbo:btcusdt')

matching_engine = MatchingEngine(orderupdates_redis_subscriber, okxbbo_redis_subscriber,htxbbo_redis_subscriber)



def runorderupdatessubscriber():
    orderupdates_redis_subscriber.start()

def runokxsubscriber():
    okxbbo_redis_subscriber.start()

def runhtxsubscriber():
    htxbbo_redis_subscriber.start()

def mainComparingengine():
    matching_engine.start()

# Start the event loop for Huobi in a thread
if __name__ == '__main__':

        # Start the Redis subscriber in a separate thread
    orderupdate_redis_thread = threading.Thread(target=runorderupdatessubscriber)
    orderupdate_redis_thread.start()

    okx_redis_thread = threading.Thread(target=runokxsubscriber)
    okx_redis_thread.start()

    htx_redis_thread = threading.Thread(target=runhtxsubscriber)
    htx_redis_thread.start()

    # Start the HTTX WebSocket client in the main thread
    asyncio.run(mainComparingengine())

    # Wait for the Huobi thread to finish (this may block indefinitely)
    okx_redis_thread.join()
    orderupdate_redis_thread.join()
    # Keep the main thread alive to allow the subscriber to continue running