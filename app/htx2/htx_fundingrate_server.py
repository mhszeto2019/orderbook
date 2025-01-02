from flask import Flask,request
from flask_socketio import SocketIO, emit
import asyncio
import websockets
import json
import threading
import configparser
import os
import sys
from flask_cors import CORS  # Import CORS
from multiprocessing import Process
import requests

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

@app.route("/get_funding_rate")
def get_funding_rate():
    # Define the URL for the Huobi API
    # Request parameters (you can customize payload and headers if needed)
    payload = {}
    headers = {}

    try:
        print("Getting funding rate...")
        contract_code = request.args.get('contract_code')
        print(contract_code)
        url = f'https://api.hbdm.com/swap-api/v1/swap_funding_rate?contract_code={contract_code}'

        # Make the API request to get the funding rate
        response = requests.get(url, headers=headers, params=payload)
        data_to_client = dict({"status":None})
        # Check if the response status is OK (200)
        if response.status_code == 200 and contract_code:
            # Parse the response as JSON
            response_data = response.json()
            latest_row = response_data.get("data","No data found")
            funding_rate = latest_row.get('funding_rate','-')
            fundingTime = unix_ts_to_datetime(latest_row.get('funding_time','-'))
            ts = unix_ts_to_datetime(response_data.get('ts'))
            ccy = standardised_ccy_naming(contract_code)
            
            if ccy in {"btcusd"}:
                    ccy = "coin-m"

            data_to_client = {"exchange":"htx","ccy":ccy,"funding_rate": f"{round(float(funding_rate) * 100, 6):.6f}"+"% ({})".format(fundingTime),"ts":ts}

            # Return the JSON data as a Flask response
            return json.dumps(data_to_client)
        else:
            # If not a successful response, return an error message
            # return json.dumps(data_to_client)
            return json.dumps({"error": "Failed to fetch funding rate", "status_code": response.status_code, "response": response.text}), response.status_code

    except requests.exceptions.RequestException as e:
        # Catch any exception and return an error response
        print('error')
