
import json
import threading
import asyncio
import websockets
import datetime
import gzip
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
logger.setLevel(logging.DEBUG)  # Set log level
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

def run_htx_positions():
        """Run the HtxPositions WebSocket client."""
        # access_key = 
        # secret_key = 
        access_key = 'e045967e-fbbc0636-e6d030e1-bewr5drtmh'
        secret_key = '7d4bac9e-780e3558-de6db8f8-5a0df'
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
                "topic": "orders.*"
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
        ws_client.start(notification_subs, auth=True, callback=htx_publicCallback)


def htx_publicCallback(message):
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
        print(message)
        trade = message.get('trade',[])
        print(trade)


if __name__== "__main__":
    htx_thread = threading.Thread(target=run_htx_positions, daemon=True)
    htx_thread.start()
    time.sleep(1000)