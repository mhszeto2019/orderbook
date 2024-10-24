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

config = configparser.ConfigParser()
util_folder_path = os.path.join(os.path.dirname(__file__), '../')
sys.path.insert(0, util_folder_path)

from util import decoder, unix_ts_to_datetime,standardised_ccy_naming
import time

# Initialize Flask app and Flask-SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)  # Enable CORS for all origins
# Websocket_class = os.path.join(util_folder_path,'htx/Websocket_class.py')
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))

from Websocket_class import WsLivePrices, Ws_orderbook, WsFutures, WsSwaps,Ws_orderbook_swaps

# print('*****************\nstart Spot ws.\n')
host = 'api.huobi.pro'
path = '/ws'

liveprice_ws = WsLivePrices(host, path,socketio)
liveprice_ws.open()

liveprice_futures_ws = WsFutures("api.hbdm.com",'/ws_index',socketio)
liveprice_futures_ws.open()

# COIN M
liveprice_swap_ws = WsSwaps("api.hbdm.com",'/swap-ws',socketio)
liveprice_swap_ws.open()

import uuid
import datetime
# sub
async def websocket_handler():
  
    # swap
    # ct = datetime.datetime.now()
    # ct_1min_prior = ct + datetime.timedelta(minutes=-1)
    
    # swap_params_list = [{"sub":"market.BTC-USD.kline.1min"}]
    
    # for normal spots
    sub_params_list = [{'sub': "market.btcusdt.ticker"},{'sub': "market.btcusdc.ticker"}]
    for sub_params in sub_params_list:
        liveprice_ws.sub(sub_params)

    # for coin-m 
    swap_params_list = [{"sub":"market.BTC-USD.kline.1min"}]
    for swap_params in swap_params_list:
        liveprice_swap_ws.sub(swap_params)


    time.sleep(10000)
    liveprice_ws.close()
    liveprice_swap_ws.close()
    # htx_swap_depth_ws.close()
    # print('end Spot ws.\n')


def start_websocket_handler():
    asyncio.run(websocket_handler())

def run_htx_client():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(websocket_handler())

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
    print("Client disconnected")

@socketio.on('message')
def handle_message(data):
    print('Received message: ' + str(data))
    # Echo the message back
    socketio.send(data)

if __name__ == "__main__":

    # Start the Flask-SocketIO server
    socketio.run(app, host='127.0.0.1', port=5012)