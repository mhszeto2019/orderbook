from flask import Flask
from flask_socketio import SocketIO, emit
import asyncio
import websockets
import json
import threading
import configparser
import os
import sys
import redis  # Redis for caching
from flask_cors import CORS  # Import CORS
from multiprocessing import Process
from gevent import monkey; monkey.patch_all()  # Ensure gevent is compatible with standard libraries
import gevent

config = configparser.ConfigParser()
util_folder_path = os.path.join(os.path.dirname(__file__), '../')
sys.path.insert(0, util_folder_path)

from util import decoder, unix_ts_to_datetime,standardised_ccy_naming
import time

# Initialize Flask app and Flask-SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app, cors_allowed_origins="*")
socketio = SocketIO(app, cors_allowed_origins="*",async_mode='gevent')
CORS(app)  # Enable CORS for all origins
# Websocket_class = os.path.join(util_folder_path,'htx/Websocket_class.py')
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))

from .Websocket_class import WsLivePrices, Ws_orderbook, WsFutures, WsSwaps,Ws_orderbook_swaps

# print('*****************\nstart Spot ws.\n')
host = 'api.huobi.pro'
path = '/ws'
loop = None

liveprice_ws = WsLivePrices(host, path,socketio)
# liveprice_ws.open()

liveprice_futures_ws = WsFutures("api.hbdm.com",'/ws_index',socketio)
# liveprice_futures_ws.open()

# COIN M
liveprice_swap_ws = WsSwaps("api.hbdm.com",'/swap-ws',socketio)
# liveprice_swap_ws.open()

import uuid
import datetime
# sub
async def websocket_handler():
    try:
        # Open WebSocket connections
        liveprice_ws.open()
        liveprice_futures_ws.open()
        liveprice_swap_ws.open()

        # Subscribe to normal market data
        sub_params_list = [
            {'sub': "market.btcusdt.ticker"},
            {'sub': "market.btcusdc.ticker"}
        ]
        for sub_params in sub_params_list:
            liveprice_ws.sub(sub_params)
        # Subscribe to swap market data
        swap_params_list = [{"sub": "market.BTC-USD.kline.1min"}]
        for swap_params in swap_params_list:
            liveprice_swap_ws.sub(swap_params)
        # while True:  # Keep the WebSocket connection alive
        #     await asyncio.sleep(1)

    except Exception as e:
        print(f"Error in WebSocket handler: {e}")

    finally:
        # Ensure that WebSocket connections are closed properly
        print(liveprice_futures_ws._has_open)

        # Attempt to reconnect
        print("Attempting to reconnect...")
        await asyncio.sleep(5)  # Wait before reconnecting
        # await websocket_handler()  # Recursive call to reconnect

async def close_connections():
    if liveprice_ws._has_open:
            liveprice_ws.close()
    if liveprice_futures_ws._has_open:
        liveprice_futures_ws.close
    if liveprice_swap_ws._has_open:
        liveprice_swap_ws.close()
    print("connections_closed")
    return "Connections closed"

async def start_websocket_handler():
    # asyncio.run(websocket_handler())
    await websocket_handler()


def run_htx_client():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_websocket_handler())

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    # Start the WebSocket client using a background task
    socketio.start_background_task(run_htx_client)

@socketio.on('disconnect')
def handle_disconnect():
    close_connections()
    
    global loop
    if loop and loop.is_running():
        # Schedule the loop to stop
        loop.call_soon_threadsafe(loop.stop)
        loop.close()  # Ensure the loop is properly closed
        loop = None 
    print("Client disconnected")

@socketio.on('message')
def handle_message(data):
    print('Received message: ' + str(data))
    # Echo the message back
    socketio.send(data)

# if __name__ == "__main__":
#     # Start the Flask-SocketIO server
#     socketio.run(app, host='0.0.0.0', port=5012)