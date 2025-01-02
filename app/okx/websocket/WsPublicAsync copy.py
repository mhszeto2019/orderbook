import asyncio
import json
import logging

from okx.websocket.WebSocketFactory import WebSocketFactory

# logging.basicConfig(level=logging.INFO)
import os
LOG_DIR = '/var/www/html/orderbook/logs'
log_filename = os.path.join(LOG_DIR, f'orderbooks_okx_data.log')

# Ensure the log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filename),  # Log to the specified file
        logging.StreamHandler()            # Optionally, also log to the console
    ]
)
file_handler = logging.FileHandler(log_filename)
console_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger = logging.getLogger("WsPublic")
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.setLevel(logging.ERROR)


class WsPublicAsync:
    def __init__(self, url):
        self.url = url
        self.subscriptions = set()
        self.callback = None
        self.loop = asyncio.get_event_loop()
        self.factory = WebSocketFactory(url)
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10  # Limit reconnect attempts
        self.reconnect_delay = 1  # Initial delay in seconds

    # async def connect(self):
    #     self.websocket = await self.factory.connect()
   

    async def connect(self):
        while self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.websocket = await self.factory.connect()
                self.reconnect_attempts = 0  # Reset on successful connection
                logger.info("Connected to WebSocket.")
                break
            except Exception as e:
                self.reconnect_attempts += 1
                delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))  # Exponential backoff
                logger.error(f"Connection failed (attempt {self.reconnect_attempts}): {e}. Retrying in {delay}s...")
                await asyncio.sleep(min(delay, 30))  # Cap delay at 30 seconds
        else:
            logger.error("Max reconnection attempts reached. Could not connect.")
            raise ConnectionError("Failed to connect to WebSocket after multiple attempts.")


    async def consume(self):
        async for message in self.websocket:
            # logger.info("Received message: {%s}", message)
            
            if self.callback:
                self.callback(message)

    async def subscribe(self, params: list, callback):
        self.callback = callback
        payload = json.dumps({
            "op": "subscribe",
            "args": params
        })
        await self.websocket.send(payload)
        # await self.consume()

    async def unsubscribe(self, params: list, callback):
        self.callback = callback
        payload = json.dumps({
            "op": "unsubscribe",
            "args": params
        })
        logger.info(f"unsubscribe: {payload}")
        await self.websocket.send(payload)

    async def stop(self):
        await self.factory.close()
        self.loop.stop()

    async def start(self):
        logger.info("Connecting to WebSocket...")
        await self.connect()
        self.loop.create_task(self.consume())

    def stop_sync(self):
        self.loop.run_until_complete(self.stop())
