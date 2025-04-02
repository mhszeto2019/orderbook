
import websockets
from okx.websocket.WsPublicAsync import WsPublicAsync
import json
import asyncio
from websockets.exceptions import ConnectionClosedError
from websockets.exceptions import ConnectionClosed
import hmac
import base64
import hashlib
import gzip
import threading
import urllib.parse
import datetime
import traceback
import os
# Logger 
from pathlib import Path
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
logger = logging.getLogger('ConnectionHelper')
logger.setLevel(logging.DEBUG)  # Set log level
# Add the file handler to the logger
logger.addHandler(file_handler)

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
        try:
            """Subscribe to a specific channel and instrument ID."""
            arg = {"channel": channel, "instId": inst_id}
            self.subscribed_pairs.append(inst_id)  # Track the subscription
            await self.ws.subscribe([arg], callback)  # Subscribe using the args list

        except Exception as e:
            logger.error("SUBSCRIBE EXCEPTION RAISED!")
            raise Exception

    async def run(self, channel, currency_pairs, callback):
        """Run the WebSocket client with automatic reconnection."""
        self.is_running = True
        retry_attempts = 0
        while self.is_running:

            try:
                # print("🔌 Connecting to WebSocket...")
                await self.start()

                for pair in currency_pairs:
                    try:
                        await self.subscribe(channel, pair, callback)
                    except Exception as e:
                        print('subscribe fail')
                        await self.unsubscribe()
                        await self.subscribe(channel,pair,callback)

                # print("✅ Subscribed! Listening for messages...")

                # while self.is_running:
                await asyncio.sleep(100)  # Keep the loop alive

            except (ConnectionClosedError, asyncio.CancelledError) as e:
                print(f"⚠️ WebSocket disconnected: {traceback.format_exc()}. Retrying...")
                retry_attempts += 1

            except Exception as e:
                print(f"❌ Unexpected error: {traceback.format_exc()}. Retrying...")
                retry_attempts += 1

            finally:
                await self.close()
                sleep_time = min(2 ** retry_attempts, 60)  # Exponential backoff
                print(f"🔄 Reconnecting in {sleep_time} seconds...")
                await asyncio.sleep(sleep_time)

    async def unsubscribe(self,callback):
        """Unsubscribe from all channels."""
        if self.ws:
            print("Unsubscribing from all channels...")
            await self.ws.unsubscribe(self.subscribed_pairs,callback)

    async def close(self):
        """Close the WebSocket connection."""
        if self.ws:
            await self.ws.factory.close()
            print("WebSocket connection closed.")
   
class HtxPositions:
    def __init__(self, url, endpoint, access_key, secret_key,username,algoname):
        self.url = url+endpoint
        self.endpoint = endpoint
        self.accesskey = access_key
        self.secretkey = secret_key
        self.is_open = False
        self.ws = None
        self._stop_event = threading.Event()
        self.loop = None
        self.thread = None
        self.username = username
        self.algoname = algoname
        
    async def start(self, subs, auth=False, callback=None):
        try:
            """ Start the subscription process in a separate thread. """
            self.is_open = True
   
            await self._run(subs,auth,callback)
        except Exception as e:
            logger.error(f"Exception error {traceback.format_exc()}")

    # def stop(self):
    #     """ Stop the subscription process. """
    #     self.is_open = False
    #     self._stop_event.set()
     
    #     self.thread.join(timeout=5)  # Allow the thread to exit gracefully

    async def _run(self, subs, auth=False, callback=None):
        """ Run the WebSocket subscription in a new event loop. """
        self.loop =  asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            await self._subscribe(subs, auth, callback)
        except Exception as e:
            print(f"An error occurred: {traceback.format_exc()}")
    

    async def _subscribe(self, subs, auth=False, callback=None):
        try:
            async for websocket in websockets.connect(self.url):
                self.ws = websocket
                if auth:
                    await self.authenticate(websocket)

                # Send all subscriptions
                for sub in subs:
                    sub_str = json.dumps(sub)
                    await websocket.send(sub_str)
                    print(f"send: {sub_str}")

                # while self.is_open and not self._stop_event.is_set():
                while self.is_open:

                    try:
                        rsp = await websocket.recv()
                        data = json.loads(gzip.decompress(rsp).decode())
                        if "op" in data and data.get("op") == "ping":
                            pong_msg = {"op": "pong", "ts": data.get("ts")}
                            await websocket.send(json.dumps(pong_msg))
                            # print(f"send: {pong_msg}")
                        if "ping" in data:
                            pong_msg = {"pong": data.get("ping")}
                            await websocket.send(json.dumps(pong_msg))
                            # print(f"send: {pong_msg}")
                        if callback:
                            callback(data)
                            logger.debug(f"{self.username}|{self.algoname}| positions data:{data}")
                            
                    except websockets.ConnectionClosed:
                        # print(" HTX WebSocket connection closed.")
                        logger.error("HTX Websocket in HTXposition connection closed")
                        # await self._close()
                        # logger.debug("CLOSED")
                        # logger.debug('REOPENING')
                        # continue
                        # self.is_open = False
                        break  # Break out of the loop when connection is closed

        except Exception as e:
            # print(f"An error occurred: {traceback.format_exc()}")
            logger.error(f"Exception:,{traceback.format_exc()}")
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

    async def _close(self):
        if self.ws:
            await self.ws.close()
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



class HtxBbo:
    def __init__(self, url, endpoint, access_key, secret_key,username,algoname):
        self.url = url+endpoint
        self.endpoint = endpoint
        self.accesskey = access_key
        self.secretkey = secret_key
        self.is_open = False
        self.ws = None
        self._stop_event = threading.Event()
        self.loop = None
        self.thread = None
        self.subs = None
        self.username = username
        self.algoname = algoname 

    async def start(self, subs, auth=False, callback=None):
        try:
            """ Start the subscription process in a separate thread. """
            # if self.thread and self.thread.is_alive():
            #     print("Already running. Please stop the current thread first.")
            #     return
            # self._stop_event = threading.Event()
            self.is_open = True
            # self.thread = threading.Thread(target=self._run, args=(subs, auth, callback))
            # self.thread.start()
            await self._run(subs,auth,callback)

        except Exception as e:
            logger.error(f"Exception error {traceback.format_exc()}")


    async def _run(self, subs, auth=False, callback=None):
        """ Run the WebSocket subscription in a new event loop. """
        self.loop =  asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            await self._subscribe(subs, auth, callback)
        except Exception as e:
            print(f"An error occurred: {traceback.format_exc()}")
       
    async def _subscribe(self, subs, auth=False, callback=None):
        try:
            async for websocket in websockets.connect(self.url):
                try:
                    self.ws = websocket
                    if auth:
                        await self.authenticate(websocket)
                    self.subs = subs
                    # Send all subscriptions
                    for sub in subs:
                        sub_str = json.dumps(sub)
                        await websocket.send(sub_str)

                        print(f"send: {sub_str}")
                except ConnectionClosed:
                    print("HTXBBO WebSocket connection closed.1")

                    # await self._close()
                    continue


                # while self.is_open and not self._stop_event.is_set():
                while self.is_open:

                    try:
                        rsp = await websocket.recv()
                        data = json.loads(gzip.decompress(rsp).decode())
                        if "op" in data and data.get("op") == "ping":
                            pong_msg = {"op": "pong", "ts": data.get("ts")}
                            await websocket.send(json.dumps(pong_msg))
                            # print(f"send: {pong_msg}")
                        if "ping" in data:
                            pong_msg = {"pong": data.get("ping")}
                            await websocket.send(json.dumps(pong_msg))
                            # print(f"send: {pong_msg}")
                        if callback:
                            callback(data)
                            logger.debug(f"{self.username}|{self.algoname}| htxbbo data:{data}")

                    except websockets.ConnectionClosed:
                        print("HTXBBO WebSocket connection closed.")
                        break  # Break out of the loop when connection is closed

        except Exception as e:
            print(f"An error occurred: {traceback.format_exc()}")
            logger.error(f"Exception error {traceback.format_exc()}")
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

    async def _close(self):
        if self.ws:
            await self.ws.close()
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
    
