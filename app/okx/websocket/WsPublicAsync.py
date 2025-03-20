import asyncio
import json
import os
from okx.websocket.WebSocketFactory import WebSocketFactory
from websockets.exceptions import ConnectionClosed,ConnectionClosedError

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

import random

class WsPublicAsync:
    def __init__(self, url):
        self.url = url
        self.subscriptions = set()
        self.callback = None
        self.loop = asyncio.get_event_loop()
        self.factory = WebSocketFactory(url)
        self.disconnection = True

    async def connect(self):
        self.websocket = await self.factory.connect()

    async def reconnect_factory(self):
        self.factory.close()
        # new factory connection
        self.websocket = await self.factory.connect()
    

    async def consume(self):
        async for message in self.websocket:
            # logger.debug("Received message: {%s}", message)
            try:
                if self.callback:
                    self.callback(message)
            except ConnectionClosed:
                print("FACTORY CONNECTION ERROR")
                logger.error("FACTORY CONNECTINON ERROR")
                continue
            except ConnectionError:
                continue
            except ConnectionClosedError:
                continue
            


        # except Exception as e:
        #     print("CONSUME ERROR")
        #     self.reconnect_factory
            # async for message in self.websocket:
            #     # logger.debug("Received message: {%s}", message)
            #     if self.callback:
            #         self.callback(message)

    # async def subscribe(self, params: list, callback):
    #     try:
    #         self.callback = callback
    #         payload = json.dumps({
    #             "op": "subscribe",
    #             "args": params
    #         })
    #         await self.websocket.send(payload)
    #     # await self.consume()
    #     except Exception as e:
    #         raise Exception

    async def subscribe(self, params: list, callback):
        self.callback = callback
        payload = json.dumps({
            "op": "subscribe",
            "args": params
        })
        await self.websocket.send(payload)
        # await self.consume()
        
    async def unsubscribe(self, params: list, callback):
        try:
            self.callback = callback
            payload = json.dumps({
                "op": "unsubscribe",
                "args": params
            })
            logger.info(f"unsubscribe: {payload}")
            await self.websocket.send(payload)
        except Exception as e:
            print(e)

    async def stop(self):
        await self.factory.close()
        self.loop.stop()


    # async def start(self):
    #     logger.info("Connecting to WebSocket...")
    #     try:
    #         await self.connect()
    #         self.loop.create_task(self.consume())
    #         # await self.consume()  # Instead of create_task, directly await consume()
    #     except Exception as e:
    #         logger.error(f"❌ WebSocket error: {e}. Restarting...")
    #         await self.reconnect_factory()
    #         await self.connect()
    #         self.loop.create_task(self.consume())

    async def start(self):
        logger.info("Connecting to WebSocket...")
        await self.connect()
        self.loop.create_task(self.consume())



    def stop_sync(self):
        self.loop.run_until_complete(self.stop())