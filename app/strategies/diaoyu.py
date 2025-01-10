import datetime
import uuid
import urllib.parse
import json
import hmac
import base64
import hashlib
import gzip
import threading
import asyncio
import websockets
import time
import sys
# sys.path.append('/var/www/orderbook/htx2')
sys.path.append('/var/www/html/orderbook/htx2')
sys.path.append('/var/www/html/orderbook/htx2/alpha')


# from app.trading_engines.htxTradeFuturesApp import place_limit_contract_order
from app.htx2.HtxOrderClass import HuobiCoinFutureRestTradeAPI
from okx import Trade
import select
import os
import psycopg2
from okx.websocket.WsPublicAsync import WsPublicAsync
import redis
import configparser
import decimal

from pathlib import Path

# Logger 
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
logger = logging.getLogger('Diaoyu')
logger.setLevel(logging.INFO)  # Set log level
# Add the file handler to the logger
logger.addHandler(file_handler)


# CONFIG
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
config.read(config_file_path)
config_source = 'redis'
REDIS_HOST = config[config_source]['host']
REDIS_PORT = config[config_source]['port']
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# config_source = 'localdb'
config_source = config['dbchoice']['db']
dbusername = config[config_source]['username']
dbpassword = config[config_source]['password']
dbname = config[config_source]['dbname']

# for DiaoYu, positive spread means buying on HTX and selling on OKX while negative spread means selling on HTX and buying on OKX. The concept of a lead and lag exchange doesnt apply here because diaoyu's mechanism is fixed to making a limit order on htx and a market order on okx 

class OkxBbo:
    def __init__(self, url="wss://ws.okx.com:8443/ws/v5/public"):
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

    async def run(self,channel ,currency_pairs, callback):
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
            await self.ws.close()
            print("WebSocket connection closed.")

   
class HtxPositions:
    def __init__(self, url, endpoint, access_key, secret_key):
        self.url = url+endpoint
        self.endpoint = endpoint
        self.accesskey = access_key
        self.secretkey = secret_key
        self.is_open = False
        self.ws = None
        self._stop_event = threading.Event()
        self.loop = None
        self.thread = None
        
    def start(self, subs, auth=False, callback=None):
        """ Start the subscription process in a separate thread. """
        if self.thread and self.thread.is_alive():
            print("Already running. Please stop the current thread first.")
            return
        self._stop_event = threading.Event()
        self.is_open = True
        self.thread = threading.Thread(target=self._run, args=(subs, auth, callback))
        self.thread.start()

    def stop(self):
        """ Stop the subscription process. """
        self.is_open = False
        self._stop_event.set()
        print(self.loop)
        # if self.ws:
        #     self._close()
        self.thread.join(timeout=5)  # Allow the thread to exit gracefully

    def _run(self, subs, auth=False, callback=None):
        """ Run the WebSocket subscription in a new event loop. """
        self.loop =  asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(self._subscribe(subs, auth, callback))
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.loop.close()

    async def _subscribe(self, subs, auth=False, callback=None):
        try:
            async with websockets.connect(self.url) as websocket:
                self.ws = websocket
                if auth:
                    await self.authenticate(websocket)

                # Send all subscriptions
                for sub in subs:
                    sub_str = json.dumps(sub)
                    await websocket.send(sub_str)
                    # print(f"send: {sub_str}")

                while self.is_open and not self._stop_event.is_set():
                    try:
                        rsp = await websocket.recv()
                        data = json.loads(gzip.decompress(rsp).decode())
                        if "op" in data and data.get("op") == "ping":
                            pong_msg = {"op": "pong", "ts": data.get("ts")}
                            await websocket.send(json.dumps(pong_msg))
                            print(f"send: {pong_msg}")
                        if "ping" in data:
                            pong_msg = {"pong": data.get("ping")}
                            await websocket.send(json.dumps(pong_msg))
                            print(f"send: {pong_msg}")
                        if callback:
                            callback(data)
                    except websockets.ConnectionClosed:
                        print(" HTX WebSocket connection closed.")
                        self.is_open = False
                        break  # Break out of the loop when connection is closed

        except Exception as e:
            print(f"An error occurred: {e}")
            self.is_open = False

    async def authenticate(self, websocket):
        """ Perform authentication on the WebSocket.

        Args:
            websocket: The WebSocket object.
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        data = {
            "AccessKeyId": self.accesskey,
            "SignatureMethod": "HmacSHA256",
            "SignatureVersion": "2",
            "Timestamp": timestamp
        }
        sign = self.generate_signature(self.url, "GET", data, self.endpoint, self.secretkey)
        data["op"] = "auth"
        data["type"] = "api"
        data["Signature"] = sign
        msg_str = json.dumps(data)
        await websocket.send(msg_str)
        # print(f"send: {msg_str}")

    def _close(self):
        if self.ws:
            self.ws.close()
            print("WebSocket connection closed.")
            self.ws = None

    @classmethod
    def generate_signature(cls, host, method, params, request_path, secret_key):
        host_url = urllib.parse.urlparse(host).hostname.lower()
        sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
        encode_params = urllib.parse.urlencode(sorted_params)
        payload = [method, host_url, request_path, encode_params]
        payload = "\n".join(payload)
        payload = payload.encode(encoding="UTF8")
        secret_key = secret_key.encode(encoding="utf8")
        digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest)
        signature = signature.decode()
        return signature



    
class Diaoyu:
    def __init__(self,username,key,jwt_token,htx_apikey,htx_secretkey,okx_apikey,okx_secretkey,okx_passphrase,algo_type,algoname,qty,ccy,spread,lead_exchange,lag_exchange,state,instrument,cursor,contract_type=None):

        self.username = username
        self.key = key
        self.jwt_token = jwt_token
        self.algotype = algo_type
        self.algoname = algoname
        self.htx_apikey =    htx_apikey
        self.htx_secretkey = htx_secretkey
        self.htx_tradeapi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",htx_apikey,htx_secretkey)
        self.okx_tradeapi = Trade.TradeAPI(okx_apikey, okx_secretkey,okx_passphrase, False, '0')

        self.okx_api_key = okx_apikey
        self.okx_secret_key = okx_secretkey
        self.okx_passphrase = okx_passphrase

        # db
        self.dbsubscriber = None
        self.db_thread = None
        # okx
        self.loop = None
        self.okx_client = None
        self.htx_thread = None
        # from okxbbo
        self.best_bid = None
        self.best_bid_sz = None
        self.best_ask = None
        self.best_ask_sz = None
        # from htx
        self.order_id = None

        # user input
        self.qty = qty
        self.ccy = ccy
        self.spread = spread
        self.lead_exchange = lead_exchange
        self.lag_exchange = lag_exchange
        self.state = state
        self.instrument = instrument
        self.contract_type = contract_type

        # derived from okx and user input
        self.limit_buy_price = None
        self.limit_buy_size = None
        self.order_id = None
        self.htx_direction = None
        self.okx_direction = None


        self.received_data = None  # Variable to store received data

        # status
        self.htx_filled_volume = 0
        self.htx_is_filled = False

        # Switch to on and off place order
        self.okx_place_order_trigger = False
        self.htx_place_order_trigger = False

        # db connection
        self.cursor = cursor
        # throttle
        self.last_call_time = 0
        self.call_interval = 1
    # update database notification to class such that class is kept updated with the latest information from the db connection
    def update_with_notification(self, json_data):
        """Update the main class with data received from the listener."""
        print(f"Updating main class with data: {json_data},{type(json_data)}")
        # if switch off, we need to revoke the order
        print(self.order_id,'old_state',self.state,'new_state',json_data['data']['state'])
        
        

        self.received_data = json_data
        # print(json_data['data'][])
        # self.algoname = json_data['data']['algoname']
        self.qty = json_data['data']['qty']
        self.ccy = json_data['data']['ccy']
        self.spread = json_data['data']['spread']
        self.lead_exchange = json_data['data']['lead_exchange']
        self.lag_exchange = json_data['data']['lag_exchange']
        self.state = json_data['data']['state']
        # print(type(self.state),type(json_data['data']['state']))
        # print(self.state == True, json_data['data']['state'] == False)
        if json_data['data']['state'] == False:
            print("REVOKING ORDER AFTER OFF")
            # we will revoke order
            # if self.loop.is_running():
            #     # If the loop is already running, create a new task
            #     asyncio.create_task(self.revoke_order_by_id(self.order_id))
            # else:
            #     # Run the async function to completion in the current thread
            #     self.loop.run_until_complete(self.revoke_order_by_id(self.order_id))
            try:
                # Use the global loop (should already be initialized)
                loop = self.loop
                
                # Submit the async function to the global loop from a background thread
                asyncio.run_coroutine_threadsafe(self.revoke_order_by_id(), loop)
            
            except RuntimeError as e:
                print(f"Error: {e}")

    async def revoke_order_by_id(self):
        print('confirming revoke order')
        # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",self.htx_apikey,self.htx_secretkey)
        tradeApi = self.htx_tradeapi

        revoke_orders = await tradeApi.revoke_order(self.ccy,
                                body = {
                                "order_id":self.order_id,
                                "contract_code": self.ccy.replace('-SWAP','')
                                }
                            )
        print(revoke_orders)
        print('ORDER REVOKED')
        self.order_id = None
        return 
    
    # connection with okx bbo
    async def run_okx_bbo(self):
        """Run the OkxBbo WebSocket client."""
        self.okx_client = OkxBbo()
        currency_pairs = ["BTC-USD-SWAP"]  # Add more pairs as needed
        channel = "bbo-tbt"
        await self.okx_client.run(channel, currency_pairs, self.okx_publicCallback)

    # connection with htx positions and orders
    def run_htx_positions(self):
        """Run the HtxPositions WebSocket client."""
        # access_key = 
        # secret_key = 
        access_key = self.htx_apikey
        secret_key = self.htx_secretkey
        # for swaps
        notification_url = 'wss://api.hbdm.com'
        notification_endpoint = '/swap-notification'
        # for future
        notification_futures_url = 'wss://api.hbdm.com'
        notification_futures_endpoint = '/notification'
        
        notification_subs = [
            {
                "op": "sub",
                "cid": str(uuid.uuid1()),
                "topic": "matchOrders.BTC-USD"
            }
        ]
        notification_futures_subs = [
            {
                "op": "sub",
                "cid": str(uuid.uuid1()),
                "topic": "matchOrders.*"
            }
        ]
        # swap client
        ws_client = HtxPositions(notification_url, notification_endpoint, access_key, secret_key)
        ws_client.start(notification_subs, auth=True, callback=self.htx_publicCallback)
        # futures client
        # ws_futures_client = HtxPositions(notification_futures_url, notification_futures_endpoint, access_key, secret_key)
        # ws_futures_client.start(notification_futures_subs, auth=True, callback=self.htx_publicCallback)

    def start_clients(self):
        """Start both WebSocket clients."""
        # Start Htx match orders with positions in a separate thread
        self.htx_thread = threading.Thread(target=self.run_htx_positions, daemon=True)
        self.htx_thread.start()
        # Run OkxBbo in the main asyncio event loop
        asyncio.run(self.run_okx_bbo())
        

    def stop_clients(self):
        """Stop both WebSocket clients gracefully."""
        if self.okx_client:
            self.okx_client.stop()  # Assuming the OkxBbo class has a stop method
        if self.htx_thread and self.htx_thread.is_alive():
            # Implement stopping mechanism for HtxPositions if necessary
            print("Stopping HtxPositions thread... (implement specific logic as needed)")

    def okx_publicCallback(self,message):
        """Callback function to handle incoming messages."""
        json_data = json.loads(message)
        print(json_data)
        if json_data.get('data'):
            currency_pair = json_data["arg"]["instId"]
           
            self.best_bid = json_data["data"][0]["bids"][0][0]
            self.best_bid_sz = json_data["data"][0]["bids"][0][1]
            self.best_ask = json_data["data"][0]["asks"][0][0]
            self.best_ask_sz = json_data["data"][0]["asks"][0][1]
            # place limit order on lagging party e.g htx - htx requires cancel and place new order for amend
            # when place order, we need to keep track of id. 
            # order will be placed to buy on htx side
            self.limit_buy_price = float(self.best_bid) - float(self.spread)
            self.limit_buy_size = self.qty
            # time.sleep(2)
            # self.place_limit_order_htx_sync()
            limit_buy_price = float(self.best_bid) - float(self.spread)
            limit_buy_size = self.qty
            if int(self.spread) < 0:
                htx_direction = 'sell'
                okx_direction = 'buy'
            else:
                htx_direction = 'buy'
                okx_direction = 'sell'
            best_bid = json_data["data"][0]["bids"][0][0]
            # self.place_limit_order_htx_sync(self.algoname, best_bid,limit_buy_price, limit_buy_size,htx_direction,okx_direction)
            
            # Throttle: Ensure minimum interval between API calls
            current_time = time.time()
            if current_time - self.last_call_time >= self.call_interval:
                self.last_call_time = current_time
                asyncio.create_task(self.place_limit_order_htx(self.algoname, best_bid,limit_buy_price, limit_buy_size,htx_direction,okx_direction))
            #Call the asynchronous function in a blocking way
            
    # def place_limit_order_htx_sync(self,algoname, best_bid, limit_buy_price, limit_buy_size,htx_direction,okx_direction):
    #     loop = asyncio.get_event_loop()
    #     if loop.is_running():
    #         coro = self.place_limit_order_htx(algoname, best_bid,limit_buy_price, limit_buy_size,htx_direction,okx_direction)
    #         asyncio.run_coroutine_threadsafe(coro, loop)
    #     else:
    #         return loop.run_until_complete(self.place_limit_order_htx(limit_buy_price, limit_buy_size))

    async def place_limit_order_htx(self,algoname, best_bid,limit_buy_price, limit_buy_size,htx_direction,okx_direction):
        # print(f"Placing order with price: {limit_buy_price}, size: {limit_buy_size},algoname={self.algoname}")
        print(f"Attributes6: algoname={algoname}, limit_buy_price={limit_buy_price},  {best_bid}")

        # Use limit_buy_price and limit_buy_size directly instead of `self.limit_buy_price`
        if self.state:
            print(f"Attributes2: algoname={algoname}, limit_buy_price={limit_buy_price},  {best_bid}")

            try:
                # check if theres is an order_id. if dont have, it will be a new order
                if self.order_id :
                    # Extract necessary parameters from the request
                    # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",self.htx_apikey,self.htx_secretkey)
                    
                    revoke_orders = await self.htx_tradeapi.revoke_order(self.ccy,
                        body = {
                        "order_id":self.order_id,
                        "contract_code": self.ccy.replace('-SWAP','')
                        }
                    )
                    # reset after cancel
                    # print('input',data)
                    logger.info(f"User:{self.username} algo_type:{self.algotype} algo_name:{self.algoname}",revoke_orders)
                    revoke_order_data = revoke_orders.get('data', [])
                    if len(revoke_order_data['errors']) == 0:

                        # Call the asynchronous place_order function
                        result = await self.htx_tradeapi.place_order(self.ccy,body = {
                            "contract_code": self.ccy.replace('-SWAP',''),
                            "price": limit_buy_price,
                            "created_at": str(datetime.datetime.now()),
                            "volume": limit_buy_size,
                            "direction": htx_direction,
                            "offset": "open",
                            "lever_rate": 5,
                            "order_price_type": 'limit'
                        })
                        self.order_id = result['data'][0]['ordId']
                        # print(self.order_id,self.limit_buy_price,self.limit_buy_size)
                    # return revoke_order_data
                else:
                    # print("NO CURRENT ORDERS")
                    # time.sleep(0.05)
                    # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",self.htx_apikey,self.htx_secretkey)

                    result = await self.htx_tradeapi.place_order(self.ccy,body = {
                            "contract_code": self.ccy.replace('-SWAP',''),
                            "price": limit_buy_price ,
                            "created_at": str(datetime.datetime.now()),
                            "volume": limit_buy_size,
                            "direction": htx_direction,
                            "offset": "open",
                            "lever_rate": 5,
                            "order_price_type": 'limit'
                        })

                    self.order_id = result['data'][0]['ordId']
                    logger.info(f"User:{self.username} algo_type:{self.algotype} algo_name:{self.algoname}",result)
                    
            except Exception as e:
                print("EXCEPTIOPN CALLED" ,e)
                
        print('ending')


    # def place_limit_order_htx_sync(self):

    #     loop = asyncio.get_event_loop()
    #     if loop.is_running():
    #         # Create a coroutine object by calling the async function
    #         coro = self.place_limit_order_htx()
    #         # Schedule it in the existing event loop and wait for the result
    #         future = asyncio.run_coroutine_threadsafe(coro, loop)
    #     else:
    #         # If no event loop is running, run the coroutine to completion
    #         return loop.run_until_complete(self.place_limit_order_htx())
        
    # # place limit order which is a swap order NOT CONTRACT
    # async def place_limit_order_htx(self):
    #     # print(self.htx_apikey,self.htx_secretkey,self.ccy,self.limit_buy_price,self.limit_buy_size,self.username,self.algoname,self.instrument,self.state)
    #     # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",self.htx_apikey,self.htx_secretkey)
    #     # tradeApi = self.htx_tradeapi
    #     print(self.algoname,self.limit_buy_price)
    #     print(f"Attributes: algoname={self.algoname}, limit_buy_price={self.limit_buy_price},  {self.best_bid}")
        
    #     # print('algo values1',self.username,self.algoname,self.best_bid,self.best_bid_sz,self.limit_buy_price,self.limit_buy_size,self.htx_filled_volume,self.state)
    #     if int(self.spread) < 0:
    #         self.htx_direction = 'sell'
    #         self.okx_direction = 'buy'
    #     else:
    #         self.htx_direction = 'buy'
    #         self.okx_direction = 'sell'
    #     # print('algo values2',self.username,self.algoname,self.best_bid,self.best_bid_sz,self.limit_buy_price,self.limit_buy_size,self.htx_filled_volume,self.state)
        
    #     if self.state:
    #         print(f"Attributes2: algoname={self.algoname}, limit_buy_price={self.limit_buy_price},  {self.best_bid}")

    #         try:
    #             # check if theres is an order_id. if dont have, it will be a new order
    #             if self.order_id :
    #                 # Extract necessary parameters from the request
    #                 # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",self.htx_apikey,self.htx_secretkey)
                    
    #                 revoke_orders = await self.htx_tradeapi.revoke_order(self.ccy,
    #                     body = {
    #                     "order_id":self.order_id,
    #                     "contract_code": self.ccy.replace('-SWAP','')
    #                     }
    #                 )
    #                 # reset after cancel
    #                 # print('input',data)
    #                 logger.info(f"User:{self.username} algo_type:{self.algotype} algo_name:{self.algoname}",revoke_orders)
    #                 revoke_order_data = revoke_orders.get('data', [])
    #                 if len(revoke_order_data['errors']) == 0:

    #                     # Call the asynchronous place_order function
    #                     result = await self.htx_tradeapi.place_order(self.ccy,body = {
    #                         "contract_code": self.ccy.replace('-SWAP',''),
    #                         "price": self.limit_buy_price,
    #                         "created_at": str(datetime.datetime.now()),
    #                         "volume": self.limit_buy_size,
    #                         "direction": self.htx_direction,
    #                         "offset": "open",
    #                         "lever_rate": 5,
    #                         "order_price_type": 'limit'
    #                     })
    #                     self.order_id = result['data'][0]['ordId']
    #                     # print(self.order_id,self.limit_buy_price,self.limit_buy_size)
    #                 # return revoke_order_data
    #             else:
    #                 # print("NO CURRENT ORDERS")
    #                 # time.sleep(0.05)
    #                 # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",self.htx_apikey,self.htx_secretkey)

    #                 result = await self.htx_tradeapi.place_order(self.ccy,body = {
    #                         "contract_code": self.ccy.replace('-SWAP',''),
    #                         "price": self.limit_buy_price ,
    #                         "created_at": str(datetime.datetime.now()),
    #                         "volume": self.limit_buy_size,
    #                         "direction": self.htx_direction,
    #                         "offset": "open",
    #                         "lever_rate": 5,
    #                         "order_price_type": 'limit'
    #                     })

    #                 self.order_id = result['data'][0]['ordId']
    #                 logger.info(f"User:{self.username} algo_type:{self.algotype} algo_name:{self.algoname}",result)
                    
    #         except Exception as e:
    #             print("EXCEPTIOPN CALLED" ,e)
                
    #     print('ending')

    #     return result

    def htx_publicCallback(self,message):
        # we need to compare htx data with okx data. When a trade is made, we will then fire data to place trade on okx
        # from okxbbo 
        # print('htx_algo values',self.username,self.algoname,self.best_bid,self.best_bid_sz,self.limit_buy_price,self.limit_buy_size,self.htx_filled_volume,self.state)
        # from db - latest received data

        # before order filled
        # Callback received: {'op': 'notify', 'topic': 'matchOrders.btc', 'ts': 1735808008380, 'symbol': 'BTC', 'contract_code': 'BTC250328', 'contract_type': 'quarter', 'status': 3, 'order_id': 1324420309708902401, 'order_id_str': '1324420309708902401', 'client_order_id': None, 'order_type': 1, 'created_at': 1735808008362, 'trade': [], 'uid': '502448972', 'volume': 1, 'trade_volume': 0, 'direction': 'sell', 'offset': 'open', 'lever_rate': 5, 'price': 98000, 'order_source': 'api', 'order_price_type': 'limit', 'is_tpsl': 0}
        # order filled
        #Callback received: {'op': 'notify', 'topic': 'matchOrders.btc', 'ts': 1735808008450, 'symbol': 'BTC', 'contract_code': 'BTC250328', 'contract_type': 'quarter', 'status': 6, 'order_id': 1324420309708902401, 'order_id_str': '1324420309708902401', 'client_order_id': None, 'order_type': 1, 'created_at': 1735808008362, 'trade': [{'trade_id': 251300058558640, 'id': '251300058558640-1324420309708902401-1', 'trade_volume': 1, 'trade_price': 98000, 'trade_turnover': 100.0, 'created_at': 1735808008446, 'role': 'maker'}], 'uid': '502448972', 'volume': 1, 'trade_volume': 1, 'direction': 'sell', 'offset': 'open', 'lever_rate': 5, 'price': 98000, 'order_source': 'api', 'order_price_type': 'limit', 'is_tpsl': 0}
        # print(message)
        # when order matches, it will update the self.htx_filled_volume
        # status code number - 	1. Ready to submit the orders; 3. Ready to submit the orders; 3. Have sumbmitted the orders; 4. Orders partially matched; 5. Orders cancelled with partially matched; 6. Orders fully matched; 7. Orders cancelled; 

        # print(self.htx_filled_volume,self.limit_buy_size,self.htx_filled_volume == self.limit_buy_size)

        trade = message.get('trade',[])

        if trade and message['status'] in [4,5,6] and self.order_id == message['order_id']:
            filled_volume = message['trade'][0]['trade_volume']
            self.htx_filled_volume += filled_volume
            # print('htx_filled_vol',self.htx_filled_volume,filled_volume,self.limit_buy_size,self.htx_filled_volume == self.limit_buy_size)
            total_htx_filled_vol = self.htx_filled_volume
            total_limit_buy_size = self.limit_buy_size
            total_limit_buy_size_int = int(total_limit_buy_size)
            self.htx_is_filled = total_htx_filled_vol == total_limit_buy_size_int
            # When order_id that was placed matches with htx position matched order, we fire market order on leading side e.g okx
            # place market order on okx with filled volume
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If the loop is already running, create a new task
                asyncio.create_task(self.place_market_order_okx(filled_volume))
            else:
                # Run the async function to completion in the current thread
                loop.run_until_complete(self.place_market_order_okx(filled_volume))
        

      
        
        
        

    async def place_market_order_okx(self,filled_volume):
        # print("PLACing MARKET ORDER ON OKX", self.qty, self.htx_filled_volume, filled_volume)
        try:
            # Initialize TradeAPI
            # tradeApi = Trade.TradeAPI(self.okx_api_key, self.okx_secret_key, self.okx_passphrase, False, '0')
            tradeApi = self.okx_tradeapi

            result = tradeApi.place_order(
                instId= 'BTC-USD-SWAP',
                tdMode= "cross", 
                side= self.okx_direction, 
                posSide= '', 
                ordType= 'market',
                sz= filled_volume
            )
            result['data'][0]['exchange']='okx'
            # print(result)
            if result["code"] == "0":
                result['data'][0]['sCode'] = 200

                if self.htx_is_filled:
                    self.state = False
                    # print("SWITCHING OFF",self.username,self.algotype,self.algoname)
                    # reset values after fill
                    self.htx_is_filled = False
                    self.htx_filled_volume = 0 
                    self.update_db()
                    self.order_id = None


            else:
                result['data'][0]['sCode'] = 400


            # print("Order request response {}".format(result))
            logger.info(f"User:{self.username} algo_type:{self.algotype} algo_name:{self.algoname}",result)

            # logger.audit(f"Trade audit log: User={user_id}, Trade={trade_id}, Price={price}, Quantity={quantity}")
            return result
        except Exception as e:
            print(e)
    
    def update_db(self):
        # print('UPDATE DB UPON COMPLETION!!!!!!!!!!!!!!!! ',self.username,self.algotype,self.algoname)
        # input should be unique so it should be username,algo_type and algoname
        # update based on parameters. by updating here it will trigger the algo listener
        self.cursor.execute("update algo_dets set state = false where username = %s and algo_type=%s and  algo_name=%s",(self.username,self.algotype,self.algoname,))
        self.cursor.connection.commit()
        logger.info(f"User:{self.username} algo_type:{self.algotype} algo_name:{self.algoname}",'DB Updated')

        return 

if __name__ == '__main__':
    # 1 strat = 1 algo 
    # 1 class has 1 algo, okx connector , htx connector and db notification connector 
    # username , algoname
    # no longer working
   
    # strat = Diaoyu(username,key,jwt_token,apikey,secretkey,algoname,qty,ccy,spread,lead_exchange,lag_exchange,state,instrument,contract_type=None)
    try:
        print('try start')
          # strat.start_clients()
    except KeyboardInterrupt:
        print("Stopping clients...")
        # strat.stop_clients()
