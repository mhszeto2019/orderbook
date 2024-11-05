import threading
import asyncio
import time
import json
import gzip
import redis
from okx.websocket.WsPublicAsync import WsPublicAsync
import websocket
from datetime import datetime
from decimal import Decimal

class RedisClient:
    """Handles Redis storage and retrieval for WebSocket data."""
    def __init__(self, host='localhost', port=6379):
        self.redis = redis.Redis(host=host, port=port, decode_responses=True)

    def update_price(self, exchange, currency_pair, price):
        """Store the latest price and timestamp for a given exchange and currency pair in a Redis hash."""
        key = f"prices:{currency_pair}"
        timestamp = datetime.now().isoformat()
        self.redis.hset(key, mapping={f"{exchange}_price": price, f"{exchange}_timestamp": timestamp})

    def get_prices(self, currency_pair):
        """Retrieve the latest prices and timestamps for both exchanges for a given currency pair."""
        key = f"prices:{currency_pair}"
        return self.redis.hgetall(key)

class HTXWebSocketClient(threading.Thread):
    def __init__(self, host, path, currency_pair, redis_client):
        super().__init__()
        self._host = host
        self._path = path
        self.currency_pair = currency_pair
        self._ws = None
        self.redis_client = redis_client

    def run(self):
        self.open()

    def open(self):
        url = f'wss://{self._host}{self._path}'
        self._ws = websocket.WebSocketApp(url,
                                          on_open=self._on_open,
                                          on_message=self._on_msg,
                                          on_close=self._on_close,
                                          on_error=self._on_error)
        self._ws.run_forever()

    def _on_open(self, ws):
        print(f"HTX WebSocket connected for {self.currency_pair}")
        sub_str = {'sub': f'market.{self.currency_pair}.bbo'}
        self._ws.send(json.dumps(sub_str))

    def _on_msg(self, ws, message):
        plain = gzip.decompress(message).decode()
        jdata = json.loads(plain)
        if 'ping' in jdata:
            self._ws.send(plain.replace('ping', 'pong'))
        elif 'tick' in jdata:
            price = jdata['tick']['bid']  # Get the bid price
            self.redis_client.update_price("HTX", self.currency_pair, price)
            print(f"Updated HTX price in Redis for {self.currency_pair}: {price}")

    def _on_close(self, ws):
        print("HTX WebSocket closed.")

    def _on_error(self, ws, error):
        print("HTX WebSocket error:", error)

class OKXWebSocketClient(threading.Thread):
    def __init__(self, url, currency_pair, redis_client):
        super().__init__()
        self.url = url
        self.currency_pair = currency_pair
        self.redis_client = redis_client
        self.ws = WsPublicAsync(url=self.url)

    async def _connect(self):
        await self.ws.start()

    async def subscribe(self):
        arg = {"channel": "bbo-tbt", "instId": self.currency_pair}
        await self.ws.subscribe([arg], self.publicCallback)

    def publicCallback(self, message):
        if 'bbo' in message:
            price = message['bbo']['bidPx']  # Get the bid price
            self.redis_client.update_price("OKX", self.currency_pair, price)
            print(f"Updated OKX price in Redis for {self.currency_pair}: {price}")

    def run(self):
        asyncio.run(self._connect())
        asyncio.run(self.subscribe())

def check_price_match(redis_client, currency_pair, threshold=0.01, max_age=5):
    """Check if the prices from HTX and OKX match within a given threshold and time frame."""
    data = redis_client.get_prices(currency_pair)
    if not data:
        return

    htx_price = data.get("HTX_price")
    okx_price = data.get("OKX_price")
    htx_timestamp = data.get("HTX_timestamp")
    okx_timestamp = data.get("OKX_timestamp")

    if htx_price and okx_price and htx_timestamp and okx_timestamp:
        # Convert prices and timestamps to compare
        htx_price, okx_price = Decimal(htx_price), Decimal(okx_price)
        htx_time = datetime.fromisoformat(htx_timestamp)
        okx_time = datetime.fromisoformat(okx_timestamp)

        # Check if both prices are recent
        now = datetime.now()
        if (now - htx_time).seconds <= max_age and (now - okx_time).seconds <= max_age:
            price_diff = abs(htx_price - okx_price)
            if price_diff <= threshold:
                print("Price match detected. Initiating trade.")
                trigger_trade(htx_price, okx_price)
            else:
                print("Prices do not match within threshold.")
        else:
            print("Prices are outdated and cannot be compared.")

def trigger_trade(htx_price, okx_price):
    """Simulate a trade execution when price criteria match."""
    print(f"Trade executed at HTX price: {htx_price} and OKX price: {okx_price}")

def main():
    # Simulate user input for currency pair
    currency_pair = input("Enter the currency pair (e.g., BTC-USD): ").strip()
    
    # Initialize Redis client
    redis_client = RedisClient()

    # Start HTX and OKX WebSocket clients
    host_huobi = 'api.huobi.pro'
    path_huobi = '/ws'
    huobi_ws = HTXWebSocketClient(host_huobi, path_huobi, currency_pair, redis_client)
    huobi_ws.start()

    okx_ws = OKXWebSocketClient("wss://wspap.okx.com:8443/ws/v5/public", currency_pair, redis_client)
    okx_ws.start()

    # Continuously check prices from Redis
    try:
        while True:
            check_price_match(redis_client, currency_pair)
            time.sleep(1)  # Check interval
    except KeyboardInterrupt:
        print("Shutting down...")

# Run the main process
if __name__ == '__main__':
    main()
