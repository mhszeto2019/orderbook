import websocket
import threading
import time
import json
import gzip
import redis
from datetime import datetime

class RedisSubscriber:
    def __init__(self, host='localhost', port=6379, channel='order_updates'):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.channel = channel
        self.redis_data = None  # Store the latest data received

    def start(self):
        """Start the Redis subscriber and listen for messages."""
        self.pubsub.subscribe(**{self.channel: self.handle_message})
        print(f"Subscribed to Redis channel: {self.channel}")
        self.listen()

    def listen(self):
        """Listen for messages on the subscribed channel."""
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                self.handle_message(message)

    def handle_message(self, message):
        """Handle incoming messages from Redis."""
        self.redis_data = json.loads(message['data'])
        print("Received data from Redis:", self.redis_data)

class Ws:
    def __init__(self, host: str, path: str):
        self._host = host
        self._path = path
        self._active_close = False
        self._has_open = False
        self._sub_str = None
        self._ws = None
        self.htx_data = None

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
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    def _on_open(self, ws):
        print('WebSocket opened:', f'wss://{self._host}{self._path}')
        print("CurrentDatetime:{} GMT+2".format(self.getcurrentdate()))
        self._has_open = True

    def _on_msg(self, ws, message):
        plain = gzip.decompress(message).decode()
        jdata = json.loads(plain)
        if 'ping' in jdata:
            sdata = plain.replace('ping', 'pong')
            self._ws.send(sdata)
        else:
            self.htx_data = jdata  # Update the last received data
            print("Received WebSocket data:", jdata)

    def _on_close(self, ws):
        print("WebSocket closed.")
        self._has_open = False
        if not self._active_close and self._sub_str is not None:
            self.open()
            self.sub(self._sub_str)

    def _on_error(self, ws, error):
        print("WebSocket error:", error)

    def sub(self, sub_str: dict):
        if not self._has_open:
            time.sleep(1)
        self._sub_str = sub_str
        self._ws.send(json.dumps(sub_str))  # Send subscription request as JSON
        print("Subscribed with:", sub_str)

    def close(self):
        self._active_close = True
        self._sub_str = None
        self._has_open = False
        self._ws.close()

# Main code to run Redis subscriber and WebSocket listener
if __name__ == '__main__':
    # Start the Redis subscriber in a separate thread
    redis_subscriber = RedisSubscriber()
    redis_thread = threading.Thread(target=redis_subscriber.start)
    redis_thread.start()

    # Check for Redis data before starting WebSocket
    print("Waiting for data from Redis...")
    while not redis_subscriber.redis_data:
        time.sleep(1)  # Wait until Redis data is available

    # Start the WebSocket connection with the obtained Redis data
    print("Connecting to WebSocket with Redis data.")
    host = 'api.huobi.pro'
    path = '/ws'
    spot = Ws(host, path)
    spot.open()

    # Subscribe to WebSocket channel based on Redis data
    sub_params = {'sub': 'market.btcusdt.bbo'}
    spot.sub(sub_params)

    # Print WebSocket data continuously
    try:
        while True:
            if spot.htx_data:
                print("Latest WebSocket data:", spot.htx_data)
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        spot.close()
        redis_thread.join()
