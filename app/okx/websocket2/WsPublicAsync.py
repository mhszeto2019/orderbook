import asyncio
import json
import os
from okx.websocket.WebSocketFactory import WebSocketFactory
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from pathlib import Path
LOG_DIR = Path('/var/www/html/orderbook/logs')
log_filename = LOG_DIR / (Path(__file__).stem + '.log')
import os
os.makedirs(LOG_DIR, exist_ok=True)
# Set up basic logging configuration
import logging
file_handler = logging.FileHandler(log_filename)
# Set up a basic formatter

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger = logging.getLogger('WsPublicAsync')

logger.setLevel(logging.DEBUG)  # Set log level
# Add the file handler to the logger
logger.addHandler(file_handler)
from websockets.exceptions import ConnectionClosed

import random

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
 

    async def connect(self):
        """Establish a WebSocket connection with retries."""
        while self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.websocket = await self.factory.connect()
                self.reconnect_attempts = 0  # Reset on successful connection
                # logger.info("Connected to WebSocket.")
                break
            except Exception as e:
                self.reconnect_attempts += 1
                delay = min(self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)), 30)  # Cap delay at 30 seconds
                logger.error(f"Connection failed (attempt {self.reconnect_attempts}): {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
        else:
            logger.error("Max reconnection attempts reached. Could not connect.")
            raise ConnectionError("Failed to connect to WebSocket after multiple attempts.")
        
    async def consume(self):
        """Continuously consume messages from the WebSocket, handling disconnections."""
        try:
            while True:
                try:
                    async for message in self.websocket:
                        # print(f"Received(OKX): {message}")
                        if self.callback:
                            self.callback(message)
                except ConnectionClosed:
                    print("FACTORY CONNECTION ERROR")
                    logger.error("FACTORY CONNECTINON ERROR")
                    continue
                except ConnectionError:
                    continue

        except Exception as e:
            logger.error(f"Error {e}")

    async def subscribe(self, params: list, callback):
        """Subscribe to WebSocket channels."""
        self.callback = callback
        payload = json.dumps({
            "op": "subscribe",
            "args": params
        })
        await self.websocket.send(payload)
        # logger.info(f"Subscribed with payload: {payload}")

    async def unsubscribe(self, params: list, callback):
        """Unsubscribe from WebSocket channels."""
        self.callback = callback
        payload = json.dumps({
            "op": "unsubscribe",
            "args": params
        })
        logger.info(f"Unsubscribe payload: {payload}")
        await self.websocket.send(payload)

    async def stop(self):
        """Stop the WebSocket connection and event loop."""
        logger.info("Stopping WebSocket connection...")
        await self.factory.close()
        self.loop.stop()

    async def reconnect(self):
        """Re-establish the WebSocket connection."""
        logger.info("Attempting to reconnect...")
        await self.connect()  # Use the existing connect logic
        if self.subscriptions:
            await self.resubscribe()  # Resubscribe to channels

    async def resubscribe(self):
        """Resubscribe to previous subscriptions after reconnection."""
        for params in self.subscriptions:
            await self.subscribe(params, self.callback)
        logger.info("Resubscribed to all channels after reconnection.")

    async def start(self):
        """Start the WebSocket connection and begin consuming messages."""
        # logger.info("Starting WebSocket connection...")
        await self.connect()
        self.loop.create_task(self.consume())

    def stop_sync(self):
        """Stop the WebSocket connection synchronously."""
        self.loop.run_until_complete(self.stop())
    
    async def cleanup(self):
        """Clean up by unsubscribing and closing WebSocket."""
        logger.debug("CLEANING UP")
        # await self.unsubscribe()
        await self.factory.close()
        logger.debug("AFTER CLEAN UP")

    async def handle_disconnection(self):
        """Handle WebSocket disconnection."""
        try:
            await self.websocket.close()
        except Exception as e:
            logger.warning(f"Error while closing WebSocket during disconnection handling: {e}")
        await self.reconnect()
