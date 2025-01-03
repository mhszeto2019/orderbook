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
# from app.trading_engines.htxTradeFuturesApp import place_limit_contract_order
from app.htx2.HtxOrderClass import HuobiCoinFutureRestTradeAPI

import asyncio
from okx.websocket.WsPublicAsync import WsPublicAsync
import redis
import json
import os
import json
import configparser
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
# print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)
config_source = 'redis'
REDIS_HOST = config[config_source]['host']
REDIS_PORT = config[config_source]['port']
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
import requests
import pg8000
import select

config_source = 'localdb'
dbusername = config[config_source]['username']
dbpassword = config[config_source]['password']
dbname = config[config_source]['dbname']

class OkxBbo:
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
                        print("WebSocket connection closed.")
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
        print(f"send: {msg_str}")

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

import time
import select
import configparser
import os
import json
import psycopg2

class DatabaseNotificationListener:
    def __init__(self, db_config, channel, filter_username=None, filter_algoname= None, callback = None):
        """
        Initialize the DatabaseNotificationListener.

        :param config_file: Path to the configuration file.
        :param config_source: The section name in the configuration file.
        :param channel: The PostgreSQL notification channel to listen to.
        :param filter_username: Optional username to filter notifications by.
        """
        print(filter_username,filter_algoname)
        self.channel = channel
        self.filter_username = filter_username
        self.filter_algoname = filter_algoname
        self.db_config = db_config
        self.callback = callback

    def listen(self):
        """
        Start listening for PostgreSQL notifications on the specified channel.
        """
        try:
            # Connect to the PostgreSQL database
            conn = psycopg2.connect(
                                    dbname=self.db_config['database'],
                                    user=self.db_config['user'],
                                    password=self.db_config['password'],
                                    host=self.db_config['host'],
                                    port=self.db_config['port']
                                    )
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()

            # Start listening to the channel
            cur.execute(f"LISTEN {self.channel};")
            print(f"Listening for notifications on '{self.channel}'...")

            while True:
                # Wait for a notification with a timeout
                if select.select([conn], [], [], 5) == ([], [], []):
                    print("No notification received within 5 seconds.")
                    continue
                
                # Poll the connection for notifications
                conn.poll()
                while conn.notifies:
                    notify = conn.notifies.pop()
                    self._process_notification(notify)

        except Exception as e:
            print(f"Error listening for notifications: {e}")
            time.sleep(5)  # Retry delay
            self.listen()  # Retry listening

    def _process_notification(self, notify):
        """
        Process a received PostgreSQL notification.
        :param notify: The notification object.
        """
        try:
            # Parse the payload as JSON
            payload = json.loads(notify.payload)
            operation = payload.get('operation')
            data = payload.get('data')
            # username = self.filter_username
            # algoname = self.filter_algoname
            self.callback(payload)

            # Check if the username matches the filter
            if self.filter_username is None or username == self.filter_username:
                print(
                    f"Notification received for user '{username}': {operation} - {data}"
                )
            else:
                print(f"Ignored notification for user '{username}'.")

        except json.JSONDecodeError:
            print(f"Received invalid JSON payload: {notify.payload}")
    
class Diaoyu:
    def __init__(self,username,key,jwt_token,apikey,secretkey,algoname,qty,ccy,spread,lead_exchange,lag_exchange,state,instrument,contract_type=None):

        self.username = username
        self.key = key
        self.jwt_token = jwt_token
        self.algoname = algoname
        self.htx_apikey =    apikey
        self.htx_secretkey = secretkey

        self.okx_api_key = None
        self.okx_secret_key = None
        self.okx_passphrase = None

        # db
        self.dbsubscriber = None
        self.db_thread = None
        # okx
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

        self.received_data = None  # Variable to store received data

        # status
        self.htx_filled_volume = 0
        self.okx_triggered_place_order = True
        self.htx_triggered_place_order = True

    # update database notification to class such that class is kept updated with the latest information from the db connection
    def update_with_notification(self, json_data):
        """Update the main class with data received from the listener."""
        print(f"Updating main class with data: {json_data},{type(json_data)}")
    
        self.received_data = json_data
        # print(json_data['data'][])
        # self.algoname = json_data['data']['algoname']
        self.qty = json_data['data']['qty']
        self.ccy = json_data['data']['ccy']
        self.spread = json_data['data']['spread']
        self.lead_exchange = json_data['data']['lead_exchange']
        self.lag_exchange = json_data['data']['lag_exchange']
        self.state = json_data['data']['state']

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
                "topic": "orders.BTC-USD"
            },
            {
                "op": "sub",
                "cid": str(uuid.uuid1()),
                "topic": "positions.BTC-USD"
            }
            
        ]
        notification_futures_subs = [
            # {
            #     "op": "sub",
            #     "cid": str(uuid.uuid1()),
            #     "topic": "orders.*"
            # }
            # ,
            {
                "op": "sub",
                "cid": str(uuid.uuid1()),
                "topic": "matchOrders.*"
            }
            # ,
            # {
            #     "op": "sub",
            #     "cid": str(uuid.uuid1()),
            #     "topic": "positions.*"
            # }
        ]
        # swap client
        # ws_client = HtxPositions(notification_url, notification_endpoint, access_key, secret_key)
        # ws_client.start(notification_subs, auth=True, callback=self.htx_publicCallback)
        # futures client
        ws_futures_client = HtxPositions(notification_futures_url, notification_futures_endpoint, access_key, secret_key)
        ws_futures_client.start(notification_futures_subs, auth=True, callback=self.htx_publicCallback)

    # connection with db
    def subsciribe2DB(self):
        db_config = {
            'host': 'localhost',  # Replace with your host
            'user': dbusername,  # Replace with your username
            'port':'5432',
            'password': dbpassword,  # Replace with your password
            'database': dbname # Replace with your database name
        }
        channel = 'algo_dets_channel'  # Channel to listen to
        print('self2',self.username,self.algoname)
        listener = DatabaseNotificationListener(
            db_config,
            channel,
            filter_username=self.username,
            filter_algoname=self.algoname,
            callback=self.update_with_notification  # Pass the callback method
        )
        self.dbsubscriber = listener
        self.dbsubscriber.listen()  # Start listening for database notifications

    def start_clients(self):
        """Start both WebSocket clients."""
        # Start HtxPositions in a separate thread
        self.db_thread = threading.Thread(target=self.subsciribe2DB, daemon=True)
        # self.db_thread.start()
        self.htx_thread = threading.Thread(target=self.run_htx_positions, daemon=True)
        self.htx_thread.start()
        # Run OkxBbo in the main asyncio event loop
        asyncio.run(self.run_okx_bbo())
        # time.sleep(100)

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
        if json_data.get('data'):
            currency_pair = json_data["arg"]["instId"]
           
            self.best_bid = json_data["data"][0]["bids"][0][0]
            self.best_bid_sz = json_data["data"][0]["bids"][0][1]
            self.best_ask = json_data["data"][0]["asks"][0][0]
            self.best_ask_sz = json_data["data"][0]["asks"][0][1]
            # place limit order on lagging party e.g htx - htx requires cancel and place new order for amend
            # when place order, we need to keep track of id. 
            # order will be placed to buy on htx side
            self.limit_buy_price = float(self.best_ask) - float(self.spread)
            self.limit_buy_size = self.qty

            # # Call the asynchronous function in a blocking way
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If the loop is already running, create a new task
                asyncio.create_task(self.place_limit_order_htx())
            else:
                # Run the async function to completion in the current thread
                loop.run_until_complete(self.place_limit_order_htx())

    # place limit order which is a swap order NOT CONTRACT
    async def place_limit_order_htx(self):
        # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",self.htx_apikey,self.htx_secretkey)
        print(self.htx_apikey,self.htx_secretkey,self.ccy,self.limit_buy_price,self.limit_buy_size,self.username,self.algoname,self.instrument,self.contract_type)
        
        if self.okx_triggered_place_order:
            try:
                if self.order_id :
                    # Extract necessary parameters from the request
                    tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",self.htx_secretkey,self.htx_apikey)
                    revoke_orders = await tradeApi.revoke_order(self.ccy,
                        body = {
                        "order_id":self.order_id,
                        "contract_code": self.ccy
                        }
                    )
                    # print('input',data)
                    revoke_order_data = revoke_orders.get('data', [])
                    if len(revoke_order_data['errors']) == 0:
                        # Call the asynchronous place_order function
                        result = await tradeApi.place_order(self.ccy,body = {
                            "contract_code": self.ccy,
                            "price": self.limit_buy_price if self.limit_buy_price else "",
                            "created_at": str(datetime.datetime.now()),
                            "volume": self.limit_buy_size,
                            "direction": 'buy',
                            "offset": "open",
                            "lever_rate": 5,
                            "order_price_type": 'limit'
                        })
                        print(result)
                        print('order placed')
                    return revoke_order_data
                else:
                    result = await tradeApi.place_order(self.ccy,body = {
                            "contract_code": self.ccy,
                            "price": self.limit_buy_price if self.limit_buy_price else "",
                            "created_at": str(datetime.datetime.now()),
                            "volume": self.limit_buy_size,
                            "direction": 'buy',
                            "offset": "open",
                            "lever_rate": 5,
                            "order_price_type": 'limit'
                        })
                    print(result)
                    self.order_id = result['order_id']
                    print('order placed')
                    return result
                
            except Exception as e:
                print(e)
    
        # Usage example
    def htx_publicCallback(self,message):
        # we need to compare htx data with okx data. When a trade is made, we will then fire data to place trade on okx
        # from okxbbo 
        print(self.best_bid,self.best_bid_sz,self.best_ask,self.best_ask_sz)
        # from db - latest received data
        print(self.qty, self.ccy)

        # from htx 
        # when order_id that was placed matches with htx position matched order, we fire market order on leading side e.g okx
        # if order id from message # Callback received: {'op': 'notify', 'topic': 'matchOrders.btc', 'ts': 1735808008450, 'symbol': 'BTC', 'contract_code': 'BTC250328', 'contract_type': 'quarter', 'status': 6, 'order_id': 1324420309708902401, 'order_id_str': '1324420309708902401', 'client_order_id': None, 'order_type': 1, 'created_at': 1735808008362, 'trade': [{'trade_id': 251300058558640, 'id': '251300058558640-1324420309708902401-1', 'trade_volume': 1, 'trade_price': 98000, 'trade_turnover': 100.0, 'created_at': 1735808008446, 'role': 'maker'}], 'uid': '502448972', 'volume': 1, 'trade_volume': 1, 'direction': 'sell', 'offset': 'open', 'lever_rate': 5, 'price': 98000, 'order_source': 'api', 'order_price_type': 'limit', 'is_tpsl': 0}
        if self.order_id == message['trade']['id'].split('-')[1]:
            self.okx_triggered_place_order = False
            self.htx_filled_volume += message['volume']
            # place market order on okx with filled volume
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If the loop is already running, create a new task
                asyncio.create_task(self.place_market_order_kx())
            else:
                # Run the async function to completion in the current thread
                loop.run_until_complete(self.place_market_order_kx())
        
        # if specified limit volume is fulfilled, we terminate the algo and reset the values
        if self.htx_filled_volume == self.limit_buy_size:
            self.state = False
            self.htx_filled_volume = 0

        print("Callback received:", message)
        
    async def place_market_order_kx(self):
        try:
            side = 'sell'
            username = self.username
            # Get the order data from the request
            # okx_secretkey_apikey_passphrase = r.get('user:test123d:api_credentials"')
            key_string = data.get('redis_key')
            if key_string.startswith("b'") and key_string.endswith("'"):
                cleaned_key_string = key_string[2:-1]
            else:
                cleaned_key_string = key_string  # Fallback if the format is unexpected

            # Now decode the base64 string into bytes
            key_bytes = base64.urlsafe_b64decode(cleaned_key_string)
            key_bytes = cleaned_key_string.encode('utf-8')
            # You can now use the key with Fernet
            cipher_suite = Fernet(key_bytes)
            
            cache_key = f"user:{username}:api_credentials"
            # Fetch the encrypted credentials from Redis
            encrypted_data = r.get(cache_key)   
            if encrypted_data:
            # Decrypt the credentials
                decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
                api_creds_dict = json.loads(decrypted_data)
                
            # Initialize TradeAPI
            tradeApi = Trade.TradeAPI(api_creds_dict['okx_apikey'], api_creds_dict['okx_secretkey'], api_creds_dict['okx_passphrase'], False, '0')
            print("username:",username)

            result = tradeApi.place_order(
                instId= data["instId"],
                tdMode= "cross", 
                side= side, 
                posSide='', 
                ordType=  data["ordType"],
                sz= str(data["sz"]) 
            )
            result['data'][0]['exchange']='okx'
            print(result)
            if result["code"] == "0":
                result['data'][0]['sCode'] = 200

                # print("Successful order request，order_id = ",result["data"][0]["ordId"])

            else:
                result['data'][0]['sCode'] = 400

                # print("Unsuccessful order request，error_code = ",result["data"][0]["sCode"], ", Error_message = ", result["data"][0]["sMsg"])

            logger.info("Order request resposne {}".format(result))

            return result
        except Exception as e:
            print(e)
    


if __name__ == '__main__':
    # 1 strat = 1 algo 
    # 1 class has 1 algo, okx connector , htx connector and db notification connector 
    # username , algoname
    username,key,jwt_token,apikey,secretkey,algoname,qty,ccy,spread,lead_exchange,lag_exchange,state,instrument,contract_type = 'brennan','key','jwt_token','fd0bb22e-bg5t6ygr6y-57ca5a15-4ae1f','109e924e-68a4de6a-0fd08753-22dcc','test1',10,'BTC-USD',20,'OKX','HTX',False,'swap'
    strat = Diaoyu(username,key,jwt_token,apikey,secretkey,algoname,qty,ccy,spread,lead_exchange,lag_exchange,state,instrument,contract_type)
    try:
        strat.start_clients()
    except KeyboardInterrupt:
        print("Stopping clients...")
        strat.stop_clients()

    # access_key = "fd0bb22e-bg5t6ygr6y-57ca5a15-4ae1f"
    # secret_key = "109e924e-68a4de6a-0fd08753-22dcc"
    # ws.subscribe(notification_subs,auth=True)
    # time.sleep(5)
    # print('unsubsring')
    # ws.unsubscribe()
    # while True: 
    #     try:
    #         asyncio.get_event_loop().run_until_complete(subscribe(notification_url, notification_endpoint ,access_key,  secret_key, notification_subs, handle_ws_data, auth=True))
    #         # asyncio.get_event_loop().run_until_complete(subscribe(place_order_url, access_key,  secret_key, place_order_subs, handle_ws_data, auth=True))
    #     #except (websockets.exceptions.ConnectionClosed):
    #     except Exception as e:
    #         traceback.print_exc()
    #         print('websocket connection error. reconnect rightnow')



# recevie<--: {'op': 'notify', 'topic': 'orders.btc-usd', 'ts': 1734410654405, 'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1, 'price': 106426, 'order_price_type': 'limit', 'direction': 'buy', 'offset': 'open', 'status': 3, 'lever_rate': 5, 'order_id': 1318559382298243072, 'order_id_str': '1318559382298243072', 'client_order_id': None, 'order_source': 'web', 'order_type': 1, 'created_at': 1734410654384, 'trade_volume': 0, 'trade_turnover': 0, 'fee': 0, 'trade_avg_price': 0, 'margin_frozen': 0.000187924003532971, 'profit': 0, 'trade': [], 'canceled_at': 0, 'fee_asset': 'BTC', 'uid': '502448972', 'liquidation_type': '0', 'is_tpsl': 0, 'real_profit': 0}
# callback param {'op': 'notify', 'topic': 'orders.btc-usd', 'ts': 1734410654405, 'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1, 'price': 106426, 'order_price_type': 'limit', 'direction': 'buy', 'offset': 'open', 'status': 3, 'lever_rate': 5, 'order_id': 1318559382298243072, 'order_id_str': '1318559382298243072', 'client_order_id': None, 'order_source': 'web', 'order_type': 1, 'created_at': 1734410654384, 'trade_volume': 0, 'trade_turnover': 0, 'fee': 0, 'trade_avg_price': 0, 'margin_frozen': 0.000187924003532971, 'profit': 0, 'trade': [], 'canceled_at': 0, 'fee_asset': 'BTC', 'uid': '502448972', 'liquidation_type': '0', 'is_tpsl': 0, 'real_profit': 0}
# recevie<--: {'op': 'ping', 'ts': '1734410655315'}
# send: {'op': 'pong', 'ts': '1734410655315'}

# LIMIT ORDER TO POSITION
# recevie<--: {'op': 'notify', 'topic': 'orders.btc-usd', 'ts': 1734410815118, 'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1, 'price': 106587, 'order_price_type': 'limit', 'direction': 'buy', 'offset': 'open', 'status': 6, 'lever_rate': 5, 'order_id': 1318559941178667008, 'order_id_str': '1318559941178667008', 'client_order_id': None, 'order_source': 'web', 'order_type': 1, 'created_at': 1734410787632, 'trade_volume': 1, 'trade_turnover': 100.0, 'fee': 2.8146021559e-08, 'trade_avg_price': 106587.00000000006, 'margin_frozen': 0.0, 'profit': 0, 'trade': [{'trade_fee': 2.8146021559e-08, 'fee_asset': 'BTC', 'real_profit': 0, 'profit': 0, 'trade_id': 100002460772968, 'id': '100002460772968-1318559941178667008-1', 'trade_volume': 1, 'trade_price': 106587, 'trade_turnover': 100.0, 'created_at': 1734410815099, 'role': 'maker'}], 'canceled_at': 0, 'fee_asset': 'BTC', 'uid': '502448972', 'liquidation_type': '0', 'is_tpsl': 0, 'real_profit': 0}
# callback param {'op': 'notify', 'topic': 'orders.btc-usd', 'ts': 1734410815118, 'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1, 'price': 106587, 'order_price_type': 'limit', 'direction': 'buy', 'offset': 'open', 'status': 6, 'lever_rate': 5, 'order_id': 1318559941178667008, 'order_id_str': '1318559941178667008', 'client_order_id': None, 'order_source': 'web', 'order_type': 1, 'created_at': 1734410787632, 'trade_volume': 1, 'trade_turnover': 100.0, 'fee': 2.8146021559e-08, 'trade_avg_price': 106587.00000000006, 'margin_frozen': 0.0, 'profit': 0, 'trade': [{'trade_fee': 2.8146021559e-08, 'fee_asset': 'BTC', 'real_profit': 0, 'profit': 0, 'trade_id': 100002460772968, 'id': '100002460772968-1318559941178667008-1', 'trade_volume': 1, 'trade_price': 106587, 'trade_turnover': 100.0, 'created_at': 1734410815099, 'role': 'maker'}], 'canceled_at': 0, 'fee_asset': 'BTC', 'uid': '502448972', 'liquidation_type': '0', 'is_tpsl': 0, 'real_profit': 0}
# recevie<--: {'op': 'ping', 'ts': '1734410817396'}

# CLOSE POSITION
# recevie<--: {'op': 'notify', 'topic': 'orders.btc-usd', 'ts': 1734410838874, 'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1.0, 'price': 0, 'order_price_type': 'market', 'direction': 'sell', 'offset': 'close', 'status': 6, 'lever_rate': 5, 'order_id': 1318560155979558912, 'order_id_str': '1318560155979558912', 'client_order_id': None, 'order_source': 'web', 'order_type': 1, 'created_at': 1734410838790, 'trade_volume': 1, 'trade_turnover': 100.0, 'fee': -3.00415888245e-07, 'trade_avg_price': 106519.0000000001, 'margin_frozen': 0, 'profit': -5.989321048e-07, 'trade': [{'trade_fee': -3.00415888245e-07, 'fee_asset': 'BTC', 'real_profit': -5.989321048e-07, 'profit': -5.989321048e-07, 'trade_id': 100002460773958, 'id': '100002460773958-1318560155979558912-1', 'trade_volume': 1, 'trade_price': 106519, 'trade_turnover': 100.0, 'created_at': 1734410838856, 'role': 'taker'}], 'canceled_at': 0, 'fee_asset': 'BTC', 'uid': '502448972', 'liquidation_type': '0', 'is_tpsl': 0, 'real_profit': -5.989321048e-07}
# callback param {'op': 'notify', 'topic': 'orders.btc-usd', 'ts': 1734410838874, 'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1.0, 'price': 0, 'order_price_type': 'market', 'direction': 'sell', 'offset': 'close', 'status': 6, 'lever_rate': 5, 'order_id': 1318560155979558912, 'order_id_str': '1318560155979558912', 'client_order_id': None, 'order_source': 'web', 'order_type': 1, 'created_at': 1734410838790, 'trade_volume': 1, 'trade_turnover': 100.0, 'fee': -3.00415888245e-07, 'trade_avg_price': 106519.0000000001, 'margin_frozen': 0, 'profit': -5.989321048e-07, 'trade': [{'trade_fee': -3.00415888245e-07, 'fee_asset': 'BTC', 'real_profit': -5.989321048e-07, 'profit': -5.989321048e-07, 'trade_id': 100002460773958, 'id': '100002460773958-1318560155979558912-1', 'trade_volume': 1, 'trade_price': 106519, 'trade_turnover': 100.0, 'created_at': 1734410838856, 'role': 'taker'}], 'canceled_at': 0, 'fee_asset': 'BTC', 'uid': '502448972', 'liquidation_type': '0', 'is_tpsl': 0, 'real_profit': -5.989321048e-07}

# order.match
# {'op': 'notify', 'topic': 'positions.btc-usd', 'ts': 1734419182416, 'event': 'order.match', 'data': [{'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1.0, 'available': 1.0, 'frozen': 0.0, 'cost_open': 106745.10000000002, 'cost_hold': 106745.10000000002, 'profit_unreal': 7.72237654e-08, 'profit_rate': 0.00041216292800446, 'profit': 7.72237654e-08, 'position_margin': 0.000187346785457018, 'lever_rate': 5, 'direction': 'buy', 'last_price': 106753.9, 'adl_risk_percent': 1}], 'uid': '502448972'}


# order match for futures
# Callback received: {'op': 'notify', 'topic': 'matchOrders.btc', 'ts': 1735808008380, 'symbol': 'BTC', 'contract_code': 'BTC250328', 'contract_type': 'quarter', 'status': 3, 'order_id': 1324420309708902401, 'order_id_str': '1324420309708902401', 'client_order_id': None, 'order_type': 1, 'created_at': 1735808008362, 'trade': [], 'uid': '502448972', 'volume': 1, 'trade_volume': 0, 'direction': 'sell', 'offset': 'open', 'lever_rate': 5, 'price': 98000, 'order_source': 'api', 'order_price_type': 'limit', 'is_tpsl': 0}
# None None None None
# 10 BTC-USD
# Callback received: {'op': 'notify', 'topic': 'matchOrders.btc', 'ts': 1735808008450, 'symbol': 'BTC', 'contract_code': 'BTC250328', 'contract_type': 'quarter', 'status': 6, 'order_id': 1324420309708902401, 'order_id_str': '1324420309708902401', 'client_order_id': None, 'order_type': 1, 'created_at': 1735808008362, 'trade': [{'trade_id': 251300058558640, 'id': '251300058558640-1324420309708902401-1', 'trade_volume': 1, 'trade_price': 98000, 'trade_turnover': 100.0, 'created_at': 1735808008446, 'role': 'maker'}], 'uid': '502448972', 'volume': 1, 'trade_volume': 1, 'direction': 'sell', 'offset': 'open', 'lever_rate': 5, 'price': 98000, 'order_source': 'api', 'order_price_type': 'limit', 'is_tpsl': 0}