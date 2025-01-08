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
from okx import Trade
import select
import os
import psycopg2
from okx.websocket.WsPublicAsync import WsPublicAsync
import redis
import configparser
import decimal
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
config.read(config_file_path)
config_source = 'redis'
REDIS_HOST = config[config_source]['host']
REDIS_PORT = config[config_source]['port']
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

config_source = 'localdb'
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

        self.okx_api_key = okx_apikey
        self.okx_secret_key = okx_secretkey
        self.okx_passphrase = okx_passphrase

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
            #Call the asynchronous function in a blocking way
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If the loop is already running, create a new task
                asyncio.create_task(self.place_limit_order_htx())
            else:
                # Run the async function to completion in the current thread
                loop.run_until_complete(self.place_limit_order_htx())

    # place limit order which is a swap order NOT CONTRACT
    async def place_limit_order_htx(self):
        # print(self.htx_apikey,self.htx_secretkey,self.ccy,self.limit_buy_price,self.limit_buy_size,self.username,self.algoname,self.instrument,self.state)
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",self.htx_apikey,self.htx_secretkey)
        print('algo values',self.username,self.algoname,self.best_bid,self.best_bid_sz,self.limit_buy_price,self.limit_buy_size,self.htx_filled_volume,self.state)

        if int(self.spread) < 0:
            self.htx_direction = 'sell'
            self.okx_direction = 'buy'
        else:
            self.htx_direction = 'buy'
            self.okx_direction = 'sell'

        if self.state:
            try:
                # check if theres is an order_id. if dont have, it will be a new order
                if self.order_id :
                    # Extract necessary parameters from the request
                    # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",self.htx_secretkey,self.htx_apikey)
                    revoke_orders = await tradeApi.revoke_order(self.ccy,
                        body = {
                        "order_id":self.order_id,
                        "contract_code": self.ccy.replace('-SWAP','')
                        }
                    )
                    # reset after cancel
                    # print('input',data)
                    revoke_order_data = revoke_orders.get('data', [])
                    if len(revoke_order_data['errors']) == 0:
                        # Call the asynchronous place_order function
                        result = await tradeApi.place_order(self.ccy,body = {
                            "contract_code": self.ccy.replace('-SWAP',''),
                            "price": self.limit_buy_price ,
                            "created_at": str(datetime.datetime.now()),
                            "volume": self.limit_buy_size,
                            "direction": self.htx_direction,
                            "offset": "open",
                            "lever_rate": 5,
                            "order_price_type": 'limit'
                        })
                        # print('result',result)
                        # print('order placed')
                        self.order_id = result['data'][0]['ordId']
                        print(self.order_id,self.limit_buy_price,self.limit_buy_size)
                    return revoke_order_data
                else:
                    print("NO CURRENT ORDERS")
                    # print(self.ccy)
                    result = await tradeApi.place_order(self.ccy,body = {
                            "contract_code": self.ccy.replace('-SWAP',''),
                            "price": self.limit_buy_price ,
                            "created_at": str(datetime.datetime.now()),
                            "volume": self.limit_buy_size,
                            "direction": self.htx_direction,
                            "offset": "open",
                            "lever_rate": 5,
                            "order_price_type": 'limit'
                        })
                  
                    self.order_id = result['data'][0]['ordId']
                    
                    return result
                
            except Exception as e:
                print(e)
    

    def htx_publicCallback(self,message):
        # we need to compare htx data with okx data. When a trade is made, we will then fire data to place trade on okx
        # from okxbbo 
        print('algo values',self.username,self.algoname,self.best_bid,self.best_bid_sz,self.limit_buy_price,self.limit_buy_size,self.htx_filled_volume,self.state)
        # from db - latest received data

        # before order filled
        # Callback received: {'op': 'notify', 'topic': 'matchOrders.btc', 'ts': 1735808008380, 'symbol': 'BTC', 'contract_code': 'BTC250328', 'contract_type': 'quarter', 'status': 3, 'order_id': 1324420309708902401, 'order_id_str': '1324420309708902401', 'client_order_id': None, 'order_type': 1, 'created_at': 1735808008362, 'trade': [], 'uid': '502448972', 'volume': 1, 'trade_volume': 0, 'direction': 'sell', 'offset': 'open', 'lever_rate': 5, 'price': 98000, 'order_source': 'api', 'order_price_type': 'limit', 'is_tpsl': 0}
        # order filled
        #Callback received: {'op': 'notify', 'topic': 'matchOrders.btc', 'ts': 1735808008450, 'symbol': 'BTC', 'contract_code': 'BTC250328', 'contract_type': 'quarter', 'status': 6, 'order_id': 1324420309708902401, 'order_id_str': '1324420309708902401', 'client_order_id': None, 'order_type': 1, 'created_at': 1735808008362, 'trade': [{'trade_id': 251300058558640, 'id': '251300058558640-1324420309708902401-1', 'trade_volume': 1, 'trade_price': 98000, 'trade_turnover': 100.0, 'created_at': 1735808008446, 'role': 'maker'}], 'uid': '502448972', 'volume': 1, 'trade_volume': 1, 'direction': 'sell', 'offset': 'open', 'lever_rate': 5, 'price': 98000, 'order_source': 'api', 'order_price_type': 'limit', 'is_tpsl': 0}
        print(message)
        # when order matches, it will update the self.htx_filled_volume
        # status code number - 	1. Ready to submit the orders; 3. Ready to submit the orders; 3. Have sumbmitted the orders; 4. Orders partially matched; 5. Orders cancelled with partially matched; 6. Orders fully matched; 7. Orders cancelled; 

        print(self.htx_filled_volume,self.limit_buy_size,self.htx_filled_volume == self.limit_buy_size)

        trade = message.get('trade',[])
        print(trade)

        if trade and message['status'] in [4,5,6] and self.order_id == message['order_id']:
            filled_volume = message['trade'][0]['trade_volume']
            self.htx_filled_volume += filled_volume
            print('htx_filled_vol',self.htx_filled_volume,filled_volume,self.limit_buy_size,self.htx_filled_volume == self.limit_buy_size)
            # print(type(self.htx_filled_volume),type(self.limit_buy_size),type(int(self.limit_buy_size)),int(self.limit_buy_size))
            total_htx_filled_vol = self.htx_filled_volume
            total_limit_buy_size = self.limit_buy_size
            total_limit_buy_size_int = int(total_limit_buy_size)
            print(total_limit_buy_size_int)
            self.htx_is_filled = total_htx_filled_vol == total_limit_buy_size_int
            #  when order_id that was placed matches with htx position matched order, we fire market order on leading side e.g okx
            # place market order on okx with filled volume
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If the loop is already running, create a new task
                asyncio.create_task(self.place_market_order_okx(filled_volume))
            else:
                # Run the async function to completion in the current thread
                loop.run_until_complete(self.place_market_order_okx(filled_volume))
        
        # if specified limit volume is fulfilled, we terminate the algo and reset the values
      
            # self.htx_filled_volume = 0

        # print("Callback received:", message)

        # if self.htx_filled_volume == self.limit_buy_size:
            # switch off algo
            
        
        
        

    async def place_market_order_okx(self,filled_volume):
        print("PLACing MARKET ORDER ON OKX", self.qty, self.htx_filled_volume, filled_volume)
        try:
            # side = 'sell'
            # username = self.username
            # # Get the order data from the request
            # # okx_secretkey_apikey_passphrase = r.get('user:test123d:api_credentials"')
            # if key_string.startswith("b'") and key_string.endswith("'"):
            #     cleaned_key_string = key_string[2:-1]
            # else:
            #     cleaned_key_string = key_string  # Fallback if the format is unexpected

            # # Now decode the base64 string into bytes
            # key_bytes = base64.urlsafe_b64decode(cleaned_key_string)
            # key_bytes = cleaned_key_string.encode('utf-8')
            # # You can now use the key with Fernet
            # cipher_suite = Fernet(key_bytes)
            
            # cache_key = f"user:{username}:api_credentials"
            # # Fetch the encrypted credentials from Redis
            # encrypted_data = r.get(cache_key)   
            # if encrypted_data:
            # # Decrypt the credentials
            #     decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
            #     api_creds_dict = json.loads(decrypted_data)
                
            # Initialize TradeAPI
            tradeApi = Trade.TradeAPI(self.okx_api_key, self.okx_secret_key, self.okx_passphrase, False, '0')
            print("username:",self.username)

            result = tradeApi.place_order(
                instId= 'BTC-USD-SWAP',
                tdMode= "cross", 
                side= self.okx_direction, 
                posSide= '', 
                ordType= 'market',
                sz= filled_volume
            )
            result['data'][0]['exchange']='okx'
            print(result)
            if result["code"] == "0":
                result['data'][0]['sCode'] = 200

                if self.htx_is_filled:
                    self.state = False
                    print("SWITCHING OFF",self.username,self.algotype,self.algoname)
                    self.update_db()
                # print("Successful order request，order_id = ",result["data"][0]["ordId"])

            else:
                result['data'][0]['sCode'] = 400

                # print("Unsuccessful order request，error_code = ",result["data"][0]["sCode"], ", Error_message = ", result["data"][0]["sMsg"])

            print("Order request resposne {}".format(result))

            return result
        except Exception as e:
            print(e)
    
    def update_db(self):
        print('UPDATE DB UPON COMPLETION!!!!!!!!!!!!!!!! ',self.username,self.algotype,self.algoname)
        # input should be unique so it should be username,algo_type and algoname
        # update based on parameters. by updating here it will trigger the algo listener
        self.cursor.execute("update algo_dets set state = false where username = %s and algo_type=%s and  algo_name=%s",(self.username,self.algotype,self.algoname,))
        self.cursor.connection.commit()

        print('connection with db')
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
