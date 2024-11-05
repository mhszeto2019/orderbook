import websocket
import threading
import time
import json
import gzip
from datetime import datetime
import redis 

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

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
            print("ping: " + plain)
            sdata = plain.replace('ping', 'pong')
            self._ws.send(sdata)
            print("pong: " + sdata)
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
        redis_client.publish('htxbbo_channel', json.dumps(redis_data))
        print('published')
        
        # print(f"Data for {symbol} stored in Redis: {redis_data}")
        print("*************************************")
        stored_data = redis_client.hgetall(redis_key)
        print('storeddata',stored_data)
    
    def _on_close(self, ws):
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


if __name__ == '__main__':
    ################# spot
    print('*****************\nstart Spot ws.\n')
    host = 'api.huobi.pro'
    path = '/ws'
    
    spot = Ws(host, path)
    spot.open()

    # sub
    sub_params1 = {'sub': 'market.btcusdt.bbo'}
    sub_params2 = {'sub': 'market.btcusdc.bbo'}
    spot.sub(sub_params1)
    spot.sub(sub_params2)

    time.sleep(10000)
    spot.close()
    print('end Spot ws.\n')