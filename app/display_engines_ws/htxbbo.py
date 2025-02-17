import websocket
import threading
import time
import json
import gzip
from datetime import datetime
import redis 

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

class Ws:
    def __init__(self, host: str, path: str):
        self._host = host
        self._path = path
        self._active_close = False
        self._has_open = False
        self._sub_str = None
        self._ws = None

    def open(self):
        url = 'wss://{}{}'.format(self._host, self._path)
        self._ws = websocket.WebSocketApp(url,
                                          on_open=self._on_open,
                                          on_message=self._on_msg,
                                          on_close=self._on_close,
                                          on_error=self._on_error)
        t = threading.Thread(target=self._ws.run_forever, daemon=True)
        t.start()

    def getcurrentdate(self):
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        return current_date

    def _on_open(self, ws):
        print('ws open')
        print("WssHostAndPath: ", 'wss://{}{}'.format(self._host, self._path))
        current_date = self.getcurrentdate()
        print("CurrentDatetime:{} GMT+2".format(current_date))
        self._has_open = True

    def _on_msg(self, ws, message):
        # print(message)
        plain = gzip.decompress(message).decode()
        jdata = json.loads(plain)
        if 'ping' in jdata:
            # print("ping: " + plain)
            sdata = plain.replace('ping', 'pong')
            self._ws.send(sdata)
            # print("pong: " + sdata)
            return
        elif 'op' in jdata:
            opdata = jdata['op']
            if opdata == 'ping':
                sdata = plain.replace('ping', 'pong')
                # print("pong: " + sdata)
                self._ws.send(sdata)
                return
            else:
                pass
        elif 'action' in jdata:
            opdata = jdata['action']
            if opdata == 'ping':
                sdata = plain.replace('ping', 'pong')
                # print("pong: "+ sdata)
                self._ws.send(sdata)
                return
            else:
                pass
        else:
            pass
        current_date = self.getcurrentdate()
        print("CurrentDatetime:{} GMT+2".format(current_date))
        print(jdata)
        # print(json.dumps(jdata, indent=4, ensure_ascii=False))
        channel = jdata['ch']  # Channel name
        symbol = jdata['tick']['symbol']  # Currency symbol
        timestamp = jdata['ts']  # Timestamp
        sequence_id = jdata['tick']['seqId']  # Sequence ID
        ask_price = jdata['tick']['ask']  # Ask price
        ask_size = jdata['tick']['askSize']  # Ask size
        bid_price = jdata['tick']['bid']  # Bid price
        bid_size = jdata['tick']['bidSize']  # Bid size
        
        # Create a Redis key using the symbol
        redis_key = f"htxbbo:{symbol}"
        
        # Prepare the data to be stored in Redis
        redis_data = {
            "currency":symbol,
            "channel": channel,
            "ask_price": ask_price,
            "ask_size": ask_size,
            "bid_price": bid_price,
            "bid_size": bid_size,
            "timestamp": timestamp,
            "sequence_id": sequence_id
        }
        
        # Store the data in Redis using HSET (Hash Set)
        redis_client.hset(redis_key, mapping=redis_data)
        print('publishing')
        redis_client.publish(redis_key, json.dumps(redis_data))
        print('published')
        
        # print(f"Data for {symbol} stored in Redis: {redis_data}")
        print("*************************************")
        stored_data = redis_client.hgetall(redis_key)
        print('storeddata',stored_data)
    
    def _on_close(self, ws,_active_close,_sub_str):
        print("ws close.")
        self._has_open = False
        if not self._active_close and self._sub_str is not None:
            self.open()
            self.sub(self._sub_str)

    def _on_error(self, ws, error):
        print(error)

    def sub(self, sub_str: dict):
        if self._active_close:
            print('has close')
            return
        while not self._has_open:
            time.sleep(1)

        self._sub_str = sub_str
        print(sub_str)
        self._ws.send(json.dumps(sub_str))  # as json string to be send
        # print(sub_str)

    def req(self, req_str: dict):
        if self._active_close:
            print('has close')
            return
        while not self._has_open:
            time.sleep(1)

        self._ws.send(json.dumps(req_str))  # as json string to be send
        print(req_str)

    def close(self):
        self._active_close = True
        self._sub_str = None
        self._has_open = False
        self._ws.close()


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

    def _on_close(self, close_status_code, close_msg):
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

    
    @staticmethod
    def unix_ts_to_datetime(ts):
        # Convert Unix timestamp to datetime
        return datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M:%S')
    
class WsSwaps(WsBase):
    def process_tick_data(self, response_data):
        # last_price = response_data['tick'].get('close', None)
        # last_size = response_data['tick'].get('vol', None)
        symbol = response_data['ch'].split('.')[1] + '-SWAP'
        # print(symbol,response_data)
        
        ts = self.unix_ts_to_datetime(response_data['ts'])
        channel = self._host + self._path
                
        channel = response_data['ch']  # Channel name
        ask_price = response_data['tick']['ask'][0] # Ask price
        ask_size = response_data['tick']['ask'][1]  # Ask size
        bid_price = response_data['tick']['bid'] [0] # Bid price
        bid_size = response_data['tick']['bid'][1]  # Bid size
        # print(ask_price,ask_size,bid_price,bid_size)
        channel_name = channel.split('.')[2]
        # Create a Redis key using the symbol
        # redis_key = f"htxbbo:{symbol}"
        redis_key = f'htx:SWAP:{channel_name}:{symbol}'
    # htx:market.BTC-USD.bbo:BTC-USD-SWAP
        # print(redis_key)

        # Prepare the data to be stored in Redis
        redis_data = {
            "currency":symbol,
            "channel": channel,
            "ask_price": ask_price,
            "ask_size": ask_size,
            "bid_price": bid_price,
            "bid_size": bid_size,
            "timestamp": ts,
            "exchange":"htx"
        }
        print(redis_data)
        # Store the data in Redis using HSET (Hash Set)
        redis_client.hset(redis_key, mapping=redis_data)
        print('publishing')
        # redis_client.publish(redis_key, json.dumps(redis_data))
        # print('published')



if __name__ == '__main__':
    ################# spot
    print('*****************\nstart Spot ws.\n')
    host = 'api.huobi.pro'
    path = '/ws'
    swap_host = "api.hbdm.com"
    swap_path='/swap-ws'
    
    spot = Ws(host, path)
    spot.open()
    swap = WsSwaps(swap_host,swap_path)
    swap.open()

    # sub
    # sub_params1 = {'sub': 'market.btcusdt.bbo'}
    sub_params2 = {'sub': 'market.BTC-USD.bbo'}
    # spot.sub(sub_params1)
    # spot.sub(sub_params1)
    swap.sub(sub_params2)


    time.sleep(10000)
    spot.close()
    print('end Spot ws.\n')