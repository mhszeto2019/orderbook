# import ccxt.pro
# from asyncio import run


# print('CCXT Pro version', ccxt.pro.__version__)


# async def main():
#     exchange = ccxt.pro.okx({
#         'options': {
#             'watchOrderBook': {
#                 # 'depth': 'bbo-tbt',  # tick-by-tick best bidask
#                 'depth':'books5'
#             },
#         },
#     })
#     markets = await exchange.load_markets()
#     # exchange.verbose = True  # uncomment for debugging purposes if necessary
#     symbol = 'BTC-USD-SWAP'
#     while True:
#         try:
#             # -----------------------------------------------------------------
#             # use this:
#             # orderbook = await exchange.watch_order_book(symbol)
#             # print(orderbook['datetime'], symbol, orderbook['asks'][0], orderbook['bids'][0])
#             # -----------------------------------------------------------------
#             # or this:
#             tick = await exchange.watchOrderBook(symbol)
#             print(tick)
#             # print(ticker['datetime'], symbol, [ticker['ask'], ticker['askVolume']], [ticker['bid'], ticker['bidVolume']])
#             # -----------------------------------------------------------------
#         except Exception as e:
#             print(type(e).__name__, str(e))
#             break
#     await exchange.close()


# run(main())
# # main()


import json, asyncio, os, traceback
from datetime import datetime
import redis
import logging
from fastapi import FastAPI
import socketio
from pathlib import Path

# Config
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

from app.util import token_required,get_logger


logger = logging.getLogger('okxbooks')

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
from typing import List
import time
app = FastAPI()

# Store connected WebSocket clients
clients: List[WebSocket] = []

import ccxt.pro
import asyncio

sio = socketio.AsyncServer(async_mode='asgi')  


# # Helper function to broadcast a message to all connected clients
async def broadcast(message):
    for client in clients:
        try:
            await client.send_text(json.dumps(message))
        except:
            clients.remove(client)  # Remove client if it is disconnected


class OrderBookStreamer:
    def __init__(self, sio, depth):
        self.sio = sio
        self.depth = depth
        self.exchange = None
        self.running = False

    async def start(self, symbol="BTC-USD-SWAP"):
        self.exchange = ccxt.pro.htx({
            'options': {
                'watchOrderBook': {
                    'depth': self.depth
                }
            }
        })
        self.running = True
        try:
            while self.running:
                # Example fetch
                htx_symbol = symbol.replace("-SWAP","")
                orderbook = await self.exchange.watch_order_book(htx_symbol)
                # print(orderbook["bids"][0],orderbook['asks'][0])
                await broadcast({
                    "symbol": symbol,
                    "bids": orderbook["bids"][:10],
                    "asks": orderbook["asks"][:10],
                    "timestamp": orderbook["timestamp"],
                    "best_bid":orderbook['bids'][0],
                    "best_ask":orderbook['asks'][0],
                    "exchange":"htxperp"
                })
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Streamer error: {e}")
        # finally:
            # await self.cleanup()

    async def stop(self):
        self.running = False
        await self.cleanup()

    async def cleanup(self):
        if self.exchange is not None:
            await self.exchange.close()  # this closes aiohttp connector

    async def change_symbol(self, new_symbol):
        await self.stop()
        await self.start(new_symbol)

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     clients.append(websocket)

#     depth = 'books5'
#     streamer = None
#     try:
#         while True:
#             time.sleep(0.1)
#             client_text = await websocket.receive_text() 
#             # print("CONNECTION")
            
#             if 'symbol' in client_text:
#                 json_dict = json.loads(client_text)
#                 symbol = json_dict['symbol']

#                 if streamer:
#                     await streamer.stop()

#                 streamer = OrderBookStreamer(sio=sio, depth=depth)
#                 asyncio.create_task(streamer.start(symbol))

#     except WebSocketDisconnect:
#         clients.remove(websocket)
#         if streamer:
#             await streamer.stop()
#         print("Client disconnected")



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)

    depth = 'books5'
    streamer = None
    try:
        while True:
            try:
                client_text = await websocket.receive_text()
            except asyncio.CancelledError:
                break

            if 'start' in client_text:
                if streamer:
                    await streamer.stop()
                streamer = OrderBookStreamer(sio=sio, depth=depth)
                asyncio.create_task(streamer.start())

            if 'symbol' in client_text:
                print('symbol change')
                json_dict = json.loads(client_text)
                symbol = json_dict.get('symbol')

                if streamer:
                    await streamer.stop()

                streamer = OrderBookStreamer(sio=sio, depth=depth)
                asyncio.create_task(streamer.start(symbol))

            # await asyncio.sleep(0.1)  # Yield to event loop

    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        if websocket in clients:
            clients.remove(websocket)
        if streamer:
            await streamer.stop()


# async def main():
#     exchange = ccxt.pro.htx({
#         'options': {
#             'watchOrderBook': {
#                 # 'depth': 'bbo-tbt',  # tick-by-tick best bidask
#                 'depth':'books5'
#             },
#         },
#     })
#     markets = await exchange.load_markets()
#     # exchange.verbose = True  # uncomment for debugging purposes if necessary
#     symbol = 'BTC-USD'
#     while True:
#         try:
#             # -----------------------------------------------------------------
#             # use this:
#             # orderbook = await exchange.watch_order_book(symbol)
#             # print(orderbook['datetime'], symbol, orderbook['asks'][0], orderbook['bids'][0])
#             # -----------------------------------------------------------------
#             # or this:
#             tick = await exchange.watchOrderBook(symbol)
#             print(tick)
#             await sio.emit('BTC-USD-SWAP', {'hello':'helloworld'})

#             # print(ticker['datetime'], symbol, [ticker['ask'], ticker['askVolume']], [ticker['bid'], ticker['bidVolume']])
#             # -----------------------------------------------------------------
#         except Exception as e:
#             print(type(e).__name__, str(e))
#             break
#     await exchange.close()




# asyncio.create_task(main())