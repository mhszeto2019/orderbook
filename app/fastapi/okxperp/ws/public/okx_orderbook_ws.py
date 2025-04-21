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

class OrderBookStreamer:
    def __init__(self, sio, depth='books5'):
        self.sio = sio                        # socketio.AsyncServer instance
        self.depth = depth                    # depth: 'books5', 'bbo-tbt', etc.
        self.exchange = None
        self.symbol = None                    # symbol like 'BTC-USD-SWAP'
        self.running = False

    async def start(self, symbol):
        self.symbol = symbol
        self.exchange = ccxt.pro.okx({
            'options': {
                'watchOrderBook': {
                    'depth': self.depth
                }
            }
        })
        await self.exchange.load_markets()
        self.running = True

        print(f"Subscribed to {symbol} with depth {self.depth}")
        await self._stream()

    async def _stream(self):
        try:
            while self.running:
                orderbook = await self.exchange.watch_order_book(self.symbol)
                # Emit to clients via socket
                # await self.sio.emit(self.symbol, {
                #     'symbol': self.symbol,
                #     'bids': orderbook['bids'][:5],
                #     'asks': orderbook['asks'][:5],
                #     'timestamp': orderbook['timestamp']
                # })
                # print(self.symbol,{
                #     'symbol': self.symbol,
                #     'bids': orderbook['bids'][:5],
                #     'asks': orderbook['asks'][:5],
                #     'timestamp': orderbook['timestamp']
                # })
                print(self.depth)
                await broadcast({
                    'symbol': self.symbol,
                    'bids': orderbook['bids'][:5],
                    'asks': orderbook['asks'][:5],
                    'timestamp': orderbook['timestamp']
                })
                
        except Exception as e:
            print(f"[ERROR] Streaming error: {e}")
            await self.stop()

    async def stop(self):
        self.running = False
        if self.exchange:
            try:
                await self.exchange.close()
                print(f"Unsubscribed and closed connection for {self.symbol}")
            except Exception as e:
                print(f"[ERROR] while closing exchange: {e}")

    async def change_symbol(self,new_symbol:str):
        self.symbol = new_symbol 

    async def change_depth(self,new_depth:str):
        print(new_depth)
        self.depth = new_depth



# # WebSocket route for connecting to the server
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)  # Add client to the list of connected clients
    try:
        depth = 'books5'
        exchange = 'okx'
        ccy= 'BTC-USD-SWAP'
        market_type = 'PERP'
        streamer = OrderBookStreamer(sio=sio, depth=depth)

        # run class in the background 
        asyncio.create_task(streamer.start(ccy))
        
        while True:
            # print('CONNECTION')
            time.sleep(0.1)
            client_text = await websocket.receive_text()  # Receive data from the client
            print(client_text)
            print(type(client_text))
            
            # Parse it into a Python dictionary
            # print(type(parsed_data))
            if 'symbol' in client_text:
                json_dict = json.loads(client_text)
                # Change the depth dynamically based on client input
                await streamer.stop()

                await streamer.change_depth('bbo-tbt')
                await streamer.change_symbol(parsed_data['symbol'])

           

            # await streamer._stream()

            # print(parsed_data)  # {'name': 'Alice', 'age': 25}
            # if parsed_data['symbol'] != ccy or parsed_data['market_type'].lower() != "perp" or parsed_data['exchange_type'] != exchange or parsed_data['depth'] != depth:
            #     print("CHANGE IN")
            #     # Change the depth dynamically based on client input
            #     await streamer.stop()

            #     await streamer.change_depth('books-tbt')
            #     await streamer.start('BTC-USD-SWAP')

            #     await websocket.send_text(f"Depth changed to 10")

            # await streamer._stream()

            # print(f"Received message: {data}")
            # print(data)
            # logger.info(data)
            # Broadcast the received message to all connected clients

    except WebSocketDisconnect:
        clients.remove(websocket)  # Remove client from the list when disconnected
        print("Client disconnected")

# Helper function to broadcast a message to all connected clients
async def broadcast(message):
    for client in clients:
        try:
            await client.send_text(json.dumps(message))
        except:
            clients.remove(client)  # Remove client if it is disconnected



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
#             await sio.emit('BTC-USD-SWAP', {'hello':'helloworld'})

#             # print(ticker['datetime'], symbol, [ticker['ask'], ticker['askVolume']], [ticker['bid'], ticker['bidVolume']])
#             # -----------------------------------------------------------------
#         except Exception as e:
#             print(type(e).__name__, str(e))
#             break
#     await exchange.close()





# asyncio.create_task(run_stream())