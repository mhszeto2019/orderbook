


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

logger = logging.getLogger()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import asyncio
from typing import List
import time
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



import ccxt.pro
import asyncio

sio = socketio.AsyncServer(async_mode='asgi')  


# # Helper function to broadcast a message to all connected clients
async def broadcast(message,client):
    try:
        await client.send_text(json.dumps(message))
    except:
        'hello'
    # for client in clients:
    #     try:
    #         await client.send_text(json.dumps(message))
    #     except:
    #         clients.remove(client)  # Remove client if it is disconnected


class OrderBookStreamer:
    def __init__(self, sio, depth,exchange_class,market_type,websocket_client):
        self.sio = sio
        self.depth = depth
        self.market_type = market_type
        self.exchange_name = exchange_class + market_type
        self.exchange_class = exchange_class
        self.exchange = None
        self.running = False
        self.symbol = None
        self.websocket_client = websocket_client
        self.contract_formatter = {
            "deribit":100,
            "okx":1,
            "htx":1,
            "binance":1
        }

    async def start(self, symbol="BTC-USD-SWAP"):
        exchange_class = self.exchange_class.lower()  # e.g., "okx", "binance", etc.
        # Get the exchange class dynamically

        exchange_class = getattr(ccxt.pro, exchange_class)
        # print(exchange_class)
        # Instantiate the exchange
        self.exchange = exchange_class({
            'options': {
                'watchOrderBook': {
                    'depth': self.depth
                }
            }
        })
     
        self.symbol = symbol
        self.running = True
        try:
            while self.running:
                # Example fetch
                if self.exchange_class == 'htx':
                    conditional_symbol = symbol.replace("-SWAP", "")
                elif self.exchange_class == 'deribit':
                    conditional_symbol = symbol.replace("USD-SWAP", "PERPETUAL")
                elif self.exchange_class == 'binance':
                    conditional_symbol = symbol.replace("-USD-SWAP", "USD_PERP")

                else:
                    conditional_symbol = symbol

                orderbook = await self.exchange.watch_order_book(conditional_symbol)
                # self.normalize_contract_size(self.exchange_class,orderbook["bids"][:10])
                # print(orderbook)
                # print(orderbook["bids"][0],orderbook['asks'][0])
                await broadcast({
                    "symbol": f"{self.symbol}",
                    "bids": self.normalize_contract_size(self.exchange_class,orderbook["bids"][:10]),
                    "asks": self.normalize_contract_size(self.exchange_class,orderbook["asks"][:10]),
                    "timestamp": orderbook["timestamp"],
                    "best_bid":self.normalize_contract_size(self.exchange_class,[orderbook['bids'][0]]),
                    "best_ask":self.normalize_contract_size(self.exchange_class,[orderbook['asks'][0]]),
                    "exchange":self.exchange_name,
                    # 'market_type':self.market_type
                },self.websocket_client)
                # await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Streamer error: {e}")
        finally:
            # await self.exchange.close()
            # print("STOP ENSURED")
            await self.stop()

    async def stop(self):
        self.running = False
        await self.cleanup()

    async def cleanup(self):
        if self.exchange is not None:
            await self.exchange.close()  # this closes aiohttp connector

    async def change_symbol(self, new_symbol):
        # print('change symbol')
        # await self.stop()
        # await self.start(new_symbol)
        self.symbol=new_symbol

    def normalize_contract_size(self,exchange,book_arr):
        # exchange with 3 parameters px,sz
        if exchange in ['deribit','okx']:
            new_arr = []
            divisor = self.contract_formatter[exchange]
            for px,sz,_ in book_arr:
                new_arr.append([px,sz/divisor,_])
            # print(new_arr)
            return new_arr
        else:
            return book_arr


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # clients.append(websocket)

    depth = 'books5'
    streamer = None
    streamer_task = None
    try:
        while True:
            try:
                msg_from_client = await websocket.receive_text()
                # print(msg_from_client)
                json_data = json.loads(msg_from_client)
                action = json_data['action']
                ccy = json_data['ccy']
                market_type = json_data['market_type']
                exchange = json_data['exchange']
                exchange_name = exchange + market_type
              
            except asyncio.CancelledError:
                break


            if action == 'start':
                # print('start',ccy)
                if streamer_task and not streamer_task.done():
                    streamer_task.cancel()
                streamer = OrderBookStreamer(sio=sio, depth=depth,exchange_class=exchange,market_type=market_type,websocket_client=websocket)
                streamer_task = asyncio.create_task(streamer.start(ccy))
                await websocket.send_text(json.dumps({"pong":True}))

            elif action == 'stop':
                # print('stop')
                await streamer.stop()
                await websocket.send_text(json.dumps({"pong":True}))


            elif action == 'change':
               
                await streamer.stop()
                if streamer_task and not streamer_task.done():
                    streamer_task.cancel()
                    await asyncio.sleep(0.1)
                streamer = OrderBookStreamer(sio=sio, depth=depth,exchange_class=exchange,market_type=market_type,websocket_client=websocket)
                streamer_task = asyncio.create_task(streamer.start(ccy))
                await websocket.send_text(json.dumps({"pong":True}))

            elif action == 'subscribe':
                
                print('subscribe')

            elif action == 'unsubscribe':
                print('unsubscribe')

           

            elif action == 'ping':
                await websocket.send_text(json.dumps({"pong":True}))
                print('ping')

          

    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        if streamer:
            await streamer.stop()




@app.websocket("/ws2")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # clients.append(websocket)

    depth = 'books5'
    streamer = None
    streamer_task = None
    try:
        while True:
            try:
                msg_from_client = await websocket.receive_text()
                # print(msg_from_client)
                json_data = json.loads(msg_from_client)
                action = json_data['action']
                ccy = json_data['ccy']
                market_type = json_data['market_type']
                exchange = json_data['exchange']
                exchange_name = exchange + market_type
                # time.sleep(2)
                # print('connection')
                # time.sleep(2)
            except asyncio.CancelledError:
                break


            if action == 'start':
                if streamer_task and not streamer_task.done():
                    streamer_task.cancel()
                # print('start',ccy)
                streamer = OrderBookStreamer(sio=sio, depth=depth,exchange_class=exchange,market_type=market_type,websocket_client=websocket)
                streamer_task = asyncio.create_task(streamer.start(ccy))
                await websocket.send_text(json.dumps({"pong":True}))

            elif action == 'stop':
                print('stop')
                await streamer.stop()
                await websocket.send_text(json.dumps({"pong":True}))


            elif action == 'change':
                
                await streamer.stop()
                if streamer_task and not streamer_task.done():
                    streamer_task.cancel()
                streamer = OrderBookStreamer(sio=sio, depth=depth,exchange_class=exchange,market_type=market_type,websocket_client=websocket)
                streamer_task = asyncio.create_task(streamer.start(ccy))
                await websocket.send_text(json.dumps({"pong":True}))

            elif action == 'subscribe':
                
                print('subscribe')

            elif action == 'unsubscribe':
                print('unsubscribe')

            elif action == 'ping':
                await websocket.send_text(json.dumps({"pong":True}))
                print('ping')

          

    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
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