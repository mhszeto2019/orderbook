import websocket
import threading
import time
import json
import gzip
from datetime import datetime
from flask_socketio import SocketIO, emit
from util import decoder, unix_ts_to_datetime,standardised_ccy_naming,format_arr_4dp,format_arr_1dp

import redis

# Initialize Redis client
# r  = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
r = redis.Redis(host='localhost', port=6379, db=0)

class WsBase:
    def __init__(self, host: str, path: str, socketio):
        self._host = host
        self._path = path
        self.socketio = socketio
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
    def __init__(self, host: str, path: str, socketio):
        super().__init__(host, path, socketio)
        self._ws = None

    def filter_orders(self, bids, asks, deviation_percentage=0.1):
        if not bids:
            return [], []

        # Find the highest bid
        highest_bid = max(float(bid[0]) for bid in bids)
        lower_threshold = highest_bid * (1 - deviation_percentage)  # 10% below highest bid
        upper_threshold = highest_bid * (1 + deviation_percentage)  # 10% above highest bid

        # Filter bids and asks based on the thresholds
        filtered_bids = [bid for bid in bids if float(bid[0]) >= lower_threshold]
        filtered_asks = [ask for ask in asks if float(ask[0]) <= upper_threshold]
        
        return filtered_bids, filtered_asks

    def process_tick_data(self, response_data):
        bids = response_data['tick'].get('bids', [])
        asks = response_data['tick'].get('asks', [])
        
        # Filter bids and asks based on the highest bid
        # filtered_bids, filtered_asks = self.filter_orders(bids, asks)
        filtered_bids,filtered_asks = format_arr_1dp(bids), format_arr_1dp(asks)

        ccy = response_data['ch'].split('.')[1]
        ccy = self.standardised_ccy_naming(ccy)
        if ccy in {"btcusd"}:
            ccy = "coin-m"

        ts = self.unix_ts_to_datetime(response_data['ts'])

        data_to_client = {
            "exchange": "htx",
            "ccy": ccy,
            "bids": filtered_bids,
            "asks": filtered_asks,
            "ts": ts
        }
        # print(ccy)
        # print(data_to_client)

        self.socketio.emit('htx_orderbook', {'data': data_to_client})

    @staticmethod
    def standardised_ccy_naming(ccy):
        # Implement the logic for standardizing currency naming
            
        ccy = ccy.lower()
        ccy = ccy.replace('-','')
        ccy = ccy.replace('_','')
        # print("Convert {} to {}".format(ccy,ccy))
        return ccy

    @staticmethod
    def unix_ts_to_datetime(ts):
        # Convert Unix timestamp to datetime
        return datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M:%S')
    
class Ws_orderbook_swaps(WsBase):
    def __init__(self, host: str, path: str, socketio):
        super().__init__(host, path, socketio)
        self._ws = None

    def filter_orders(self, bids, asks, deviation_percentage=0.1):
        if not bids:
            return [], []

        # Find the highest bid
        highest_bid = max(float(bid[0]) for bid in bids)
        lower_threshold = highest_bid * (1 - deviation_percentage)  # 10% below highest bid
        upper_threshold = highest_bid * (1 + deviation_percentage)  # 10% above highest bid

        # Filter bids and asks based on the thresholds
        filtered_bids = [bid for bid in bids if float(bid[0]) >= lower_threshold]
        filtered_asks = [ask for ask in asks if float(ask[0]) <= upper_threshold]

        return filtered_bids, filtered_asks

    def process_tick_data(self, response_data):
        bids = response_data['tick'].get('bids', [])
        asks = response_data['tick'].get('asks', [])
        
        bidPrice,bidSize = bids[0]
        askPrice,askSize = asks[0]

        filtered_bids,filtered_asks = format_arr_1dp(bids), format_arr_1dp(asks)

        ccy = response_data['ch'].split('.')[1]
        ccy = self.standardised_ccy_naming(ccy)

        

        if ccy in {"btcusd"}:
            ccy = "coin-m"
        ts = self.unix_ts_to_datetime(response_data['ts'])

        data_to_client = {
            "exchange": "htx",
            "ccy": ccy,
            "bids": filtered_bids,
            "asks": filtered_asks,
            "bidPrice":bidPrice,
            "bidSize":bidSize,
            "askPrice":askPrice,
            "askSize":askSize,
            "ts": ts

        }
        # print(ccy)
        # print(data_to_client)
        # Create a single hash for the currency (ccy)
        r.hset(f'orderbook_htx_{ccy}', mapping={
            'bidPrice': str(bidPrice),
            'bidSize': str(bidSize),
            'askPrice': str(askPrice),
            'askSize': str(askSize)
        })
        self.socketio.emit('htx_orderbook', {'data': data_to_client})

    @staticmethod
    def standardised_ccy_naming(ccy):
        # Implement the logic for standardizing currency naming
            
        ccy = ccy.lower()
        ccy = ccy.replace('-','')
        ccy = ccy.replace('_','')
        # print("Convert {} to {}".format(ccy,ccy))
        return ccy

    @staticmethod
    def unix_ts_to_datetime(ts):
        # Convert Unix timestamp to datetime
        return datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M:%S')
    

    
class WsLivePrices(WsBase):
    def process_tick_data(self, response_data):
        # print(response_data)
        last_price = response_data['tick'].get('lastPrice', [])
        last_size = response_data['tick'].get('lastSize', [])
        bidPrice = response_data['tick'].get('bid', [])
        bidSize = response_data['tick'].get('bidSize', [])
        askPrice = response_data['tick'].get('ask', [])
        askSize = response_data['tick'].get('askSize', [])
        ccy = standardised_ccy_naming(response_data['ch'].split('.')[1])
        ts = unix_ts_to_datetime(response_data['ts'])
        channel = self._host + self._path
        data_to_client = {
            "exchange": "htx",
            "ccy": ccy,
            "lastPrice": last_price,
            "lastSize": last_size,
            "ts": ts,
            "channel":channel,
            "bidPrice":bidPrice,
            "bidSize":bidSize,
            "askPrice":askPrice,
            "askSize":askSize
        }
        # print(data_to_client)
        self.socketio.emit(f'htx_live_price_{ccy}', {'data': json.dumps(data_to_client)})


class WsFutures(WsBase):
    def process_tick_data(self, response_data):
        last_price = response_data['tick'].get('contact_price', [])
        last_size = response_data['tick'].get('lastSize', None)

        ccy = standardised_ccy_naming(response_data['ch'].split('.')[1])
        ts = unix_ts_to_datetime(response_data['ts'])
        channel = self._host + self._path

        data_to_client = {
            "exchange": "htx",
            "ccy": ccy,
            "lastPrice": last_price,
            "lastSize": last_size,
            "ts": ts,
            "channel":channel

        }
        self.socketio.emit(f'htx_live_price_{ccy}_futures', {'data': json.dumps(data_to_client)})


# FOR COIN M
class WsSwaps(WsBase):
    def process_tick_data(self, response_data):
        last_price = response_data['tick'].get('close', None)
        last_size = response_data['tick'].get('vol', None)
        ccy = standardised_ccy_naming(response_data['ch'].split('.')[1]) + 'swap'
        if ccy in {"btcusdswap"}:
                                ccy = "coin-m"
        ts = unix_ts_to_datetime(response_data['ts'])
        channel = self._host + self._path
    
        order_data_encoded = r.hgetall(f'orderbook_htx_{ccy}')
    

        # Convert byte strings to regular strings
        decoded_data = {key.decode('utf-8'): value.decode('utf-8') for key, value in order_data_encoded.items()}
        

        data_to_client = {
            "exchange": "htx",
            "ccy": ccy,
            "lastPrice": last_price,
            "lastSize": last_size,
       
            "ts": ts,
            "channel":channel

        }
        # Merge decoded data into data_to_client
        data_to_client.update(decoded_data)

        # Convert the merged data to JSON
        print(data_to_client)
        self.socketio.emit(f'htx_live_price_{ccy}', {'data': json.dumps(data_to_client)})


if __name__ == '__main__':
    ################# spot
    print('*****************\nstart Spot ws.\n')
    host = 'api.huobi.pro'
    path = '/ws'
    spot = WsSwaps(host, path)
    spot.open()


    # sub
    sub_params1 = {'sub': 'market.btcusdt.depth.step0'}
    sub_params2 = {'sub': 'market.ethusdt.depth.step0'}
    spot.sub(sub_params1)
    spot.sub(sub_params2)

    time.sleep(10000)
    spot.close()
    # print('end Spot ws.\n')