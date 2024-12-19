import datetime
import uuid
import urllib.parse
import asyncio
import websockets
import json
import hmac
import base64
import hashlib
import gzip
import datetime
import uuid
import urllib.parse
import json

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

class Diaoyu:
    def __init__(self, url, endpoint, access_key, secret_key):
        self.url = url
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
                    print(f"send: {sub_str}")

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


# Usage example
def publicCallback(message):
    print("Callback received:", message)

# def main():
access_key = "fd0bb22e-bg5t6ygr6y-57ca5a15-4ae1f"
secret_key = "109e924e-68a4de6a-0fd08753-22dcc"
notification_url = 'wss://api.hbdm.com/swap-notification'
notification_endpoint = '/swap-notification'
notification_subs = [
    {
        "op": "sub",
        "cid": str(uuid.uuid1()),
        "topic": "positions.BTC-USD"
    }
]


if __name__ == '__main__':
        
    ws1 = Diaoyu(notification_url, notification_endpoint, access_key, secret_key)
    ws1.start(notification_subs, auth=True, callback=publicCallback)
    print("SUBSCRIBING")

    # Wait for a while to allow subscription
    time.sleep(5)

    print("STOPPING")
    ws1.stop()
    time.sleep(15)

    print("RESTARTING")
    ws1.start(notification_subs, auth=True, callback=publicCallback)
    time.sleep(15)

    ws1.stop()



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