import os
import sys
sys.path.insert(0, "/home/brenn/environments/test/lib/python3.10/site-packages")
from twilio.rest import Client
import time
from twilio.twiml.voice_response import VoiceResponse
import asyncio
import threading
# Run the alert function
from datetime import datetime
import time
import pg8000
from pg8000.dbapi import ProgrammingError, DatabaseError
from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS
import traceback
import configparser
from app.htx2.HtxOrderClass import HuobiCoinFutureRestTradeAPI
from okx import Account

import logging
import sys


# Logger 
import os
from pathlib import Path
# Define the log directory and the log file name
LOG_DIR = Path('/var/www/html/orderbook/logs')
log_filename = LOG_DIR / (Path(__file__).stem + '.log')
os.makedirs(LOG_DIR, exist_ok=True)
# Set up basic logging configuration
import logging
file_handler = logging.FileHandler(log_filename)
# Set up a basic formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger = logging.getLogger('twilio_liq')
logger.setLevel(logging.DEBUG)  # Set log level
# Add the file handler to the logger
logger.addHandler(file_handler)
from datetime import datetime



config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '../..','config_folder', 'credentials.ini')
print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)

config_source = config['dbchoice']['db']
dbusername = config[config_source]['username']
dbpassword = config[config_source]['password']
dbname = config[config_source]['dbname']

# Twilio API Credentials (Replace with yours)
ACCOUNT_SID = config['twilio']['account_sid']
AUTH_TOKEN = config['twilio']['auth_token']
TWILIO_PHONE = config['twilio']['phone_number']
# TWIML_URL = "https://handler.twilio.com/twiml/EH2940b91a251c76dd1d2d52e83a4ff983"  # Replace with your TwiML URL

# Execute SELECT query to check for existing users
con = pg8000.connect(
    user=dbusername,         # Change to your PostgreSQL username
    password=dbpassword, # Change to your PostgreSQL password
    host="localhost",         # Host, usually 'localhost' for local connections
    port=5432,                # Default PostgreSQL port
    database=dbname   # Database name
)

# client = Client(ACCOUNT_SID, AUTH_TOKEN)
class TraderNotifier:

    STATES = {
        0b00: "INACTIVE",       # Not running (00)
        0b10: "ACTIVE_UNACKED", # Running + unanswered (10)
        0b11: "ACTIVE_ACKED",   # Running + answered (11)
        0b01: "RESOLVED"        # Not running but was active (01)
    }

    def __init__(self,username, ACCOUNT_SID, AUTH_TOKEN, TWILIO_PHONE, YOUR_PHONE,HTX_APIKEY,HTX_SECRETKEY,OKX_APIKEY,OKX_SECRETKEY,OKX_PASSPHRASE):
        self.client = Client(ACCOUNT_SID, AUTH_TOKEN)
        self.username = username
        self.ACCOUNT_SID = ACCOUNT_SID
        self.AUTH_TOKEN = AUTH_TOKEN
        self.TWILIO_PHONE = TWILIO_PHONE
        self.YOUR_PHONE = YOUR_PHONE
        self.htx_apikey = HTX_APIKEY
        self.htx_secretkey = HTX_SECRETKEY
        self.okx_apikey = OKX_APIKEY
        self.okx_secretkey = OKX_SECRETKEY
        self.okx_passphrase = OKX_PASSPHRASE
        self._state = 0b00

        self.get_htx_liq_px_status = True
        self.get_okx_liq_px_status = True
        self.exchanges = {}

        self.liq_alert_threshold = 0.15
        self.update_thread = None
        self.update_thread_status = False

        # self.last_prices = {} #{"BTC-USD":"80000", "ETH-USD":"1600"}
        # self.last_price_update_times = {"BTC-USD":time.time(),"ETH-USD":time.time()} #{"BTC-USD":"80000", "ETH-USD":"1600"}
        # self._state = 0b00  # Initialize as inactive
        self.latest_prices = {
                        'BTC-USD': {'ts': None, 'last_px': None, 'exchange': None},
                        'ETH-USD': {'ts': None, 'last_px': None, 'exchange': None}
                    }

        self.x= 0

    def get_htx_liq_px(self):
        try:
            if self.get_htx_liq_px_status:
                
                # Data received from the client (assuming JSON body)
                instId = "BTC-USD"
                instId_list = ["BTC-USD","ETH-USD"]
                tdMode = "cross"

                # Extract necessary parameters from the request
                tradeApi = HuobiCoinFutureRestTradeAPI(
                    "https://api.hbdm.com",
                    self.htx_apikey,
                    self.htx_secretkey
                )
                htx_liq_prices = {ccy: 0 for ccy in instId_list}
                # print(htx_liq_prices)
                for contract_code in instId_list:
                    positions = asyncio.run(tradeApi.get_positions(instId, body={"contract_code": contract_code}))
                    # Use next() to safely get the first element or default to an empty dict
                    print(positions)
                    position_data = next(iter(positions.get('data', [])), {})
                    if 'liq_px' and 'last_price' in position_data:
                        contract = position_data.get('contract_code', '')
                        htx_liq_prices[contract_code] = {"liq_px":position_data['liq_px'],"last_px":position_data['last_price'],"direction":position_data['direction'],"ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(positions['ts'] / 1000))}
                    print(f"HTX POSITIONS {position_data}")
                        


                self.exchanges['htx'] = htx_liq_prices
                return htx_liq_prices

        except Exception as e:
            print(f"ERROR {traceback.format_exc()}")

    def get_okx_liq_px(self):
        try:
            if self.get_okx_liq_px_status:
                # Data received from the client (assuming JSON body)
                instId = "BTC-USD"
                instId_list = ["BTC-USD","ETH-USD"]
                tdMode = "cross"

                okx_liq_prices = {ccy: 0 for ccy in instId_list}
                accountAPI = Account.AccountAPI(self.okx_apikey, self.okx_secretkey,self.okx_passphrase, False, '0')
                result = accountAPI.get_positions()
                if result.get('data'):
                    current_ts = datetime.now()
                    # print(result['data'])
                    for row in result['data']:
                        contract_code = row['instId'].replace('-SWAP','')
                        liq_px = row['liqPx']
                        direction = 'sell' if int(row['pos']) <0 else 'buy'
                        okx_liq_prices[contract_code] = {"liq_px":row['liqPx'],"last_px":row['last'],"direction":direction,"ts":current_ts.strftime('%Y-%m-%d %H:%M:%S')}
            

                self.exchanges['okx'] = okx_liq_prices
                
                return okx_liq_prices

        except Exception as e:
            print(f"ERROR {traceback.format_exc()}")


    def check_liq_px_distance(self,exchanges,threshold, symbol="BTC-USD"):
        """
        Check if liquidation price (liq_px) is at least 15% away from last price (last_px).
        
        :param exchanges: Dictionary containing market data from multiple exchanges.
        :param symbol: Trading pair to check (default is 'BTC-USD').
        :param threshold: Percentage threshold (default is 15% or 0.15).
        :return: Dictionary with distance checks.
        """
        results = {}

        for exchange, data in exchanges.items():
            print(f"EXCHANGE: {exchange},{data}")
            if symbol in data and isinstance(data[symbol], dict):
                try:
                    liq_px = float(data[symbol]['liq_px'])
                    last_px = float(data[symbol]['last_px'])
                    direction = data[symbol]['direction'] 
                    logger.info(f"[{self.username}]|liq_px:{liq_px}|last_px:{last_px}|direction:{direction}[ALERT WHEN {last_px * (1 - threshold) if direction =='buy' else last_px * (1 + threshold) } {'less' if direction =='buy' else 'more'  }  than liq_px]")

         
                    if direction == 'buy':
                        alert_px = last_px * (1 - threshold)
                        should_alert = alert_px <= float(liq_px)
                    else:  # direction == 'buy'
                        alert_px = last_px * (1 + threshold)
                        should_alert = alert_px >= float(liq_px)
                
                    # State transition logic
                    if should_alert:
                        if self._state != 0b10:  # Only trigger if not already active
                            logger.info(f"[{self.username}]|CALLING,position unsafe Exchange:{exchange}|Direction:{direction.upper()}|liq_px:{liq_px}|last_px{last_px}")
                            print(f"ALERT: {exchange} {direction.upper()} {alert_px:.2f} | {last_px:.2f} ")
                            self._state = 0b10  # ACTIVE_UNACKED
                            self.start_call(exchange,direction,liq_px,last_px)   
                    else:
                        print("SHOULDNT ALERT")
                        print(f"RESOLVED: {exchange} {direction.upper()} {liq_px} {last_px} position now safe")

                        if self._state & 0b10:  # If was active
                            self._state = 0b01  # RESOLVED
                            print(f"RESOLVED: {exchange} {direction.upper()} position now safe")
                 
                except (KeyError, TypeError, ValueError) as e:
                    print("EXCEPTION ",e)
                    results[exchange] = {"error": f"Invalid data format: {e}"}

        return results


    def parse_timestamp(self,ts):
        """Helper function to convert ts to a datetime object."""
        if isinstance(ts, (int, float)):
            # assume Unix timestamp, convert to datetime
            # if it's in milliseconds (e.g., 1745377162187), divide by 1000
            if ts > 1e12:
                ts = ts / 1000
            return datetime.fromtimestamp(ts)
        elif isinstance(ts, str):
            try:
                return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    return datetime.fromtimestamp(float(ts))  # fallback: try parsing as float timestamp string
                except ValueError:
                    logger.warning(f"[{self.username}]|Unrecognized timestamp format: {ts}")
                    return None
        elif isinstance(ts, datetime):
            return ts
        else:
            logger.warning(f"Unsupported timestamp type: {type(ts)}")
            return None

    def update_liq_px(self,update_interval = 10):
        while self.update_thread_status:
            htx_liq_prices = self.get_htx_liq_px()
            okx_liq_prices = self.get_okx_liq_px()
            # {'BTC-USD': {'liq_px': 122838.4771710599, 'last_px': 77067.3, 'direction': 'sell', 'ts': '2025-04-07 14:01:02'}

            # Find the latest entry with ts
           
            for exchange, symbols in self.exchanges.items():
                for symbol, info in symbols.items():
                    if symbol in self.latest_prices and isinstance(info, dict) and 'ts' in info:
                        ts = self.parse_timestamp(info['ts'])
                        current = self.parse_timestamp(self.latest_prices[symbol].get('ts'))

                        if ts and (current is None or ts > current):
                            self.latest_prices[symbol] = {
                                'ts': ts,
                                'last_px': float(info['last_px']),
                                'exchange': exchange
                            }

            logger.info(f"[{self.username}]|latest_px{self.latest_prices['BTC-USD']['last_px']}|ts:{self.latest_prices['BTC-USD']['ts']}|exchanges:{self.exchanges}")

            # if self.username in ['brennan12']:
            if self.username in ['SHWfalconstead']:

                self.exchanges['deribit'] = {'BTC-USD': {'liq_px':65000, 'last_px': self.latest_prices['BTC-USD']['last_px'], 'direction': 'buy', 'ts': current},'ETH-USD': {'liq_px': 122838.1600, 'last_px': 0, 'direction': 'buy', 'ts': '2025-04-08 11:03:02'}}

                self.exchanges['binance'] = {'BTC-USD': {'liq_px':60000, 'last_px': self.latest_prices['BTC-USD']['last_px'], 'direction': 'buy', 'ts': current},'ETH-USD': {'liq_px': 122838.1600, 'last_px': 0, 'direction': 'buy', 'ts': '2025-04-08 11:03:02'}}

                # self.exchanges['htx2'] = {'BTC-USD': {'liq_px':112000, 'last_px': self.latest_prices['BTC-USD']['last_px'], 'direction': 'sell', 'ts': current},'ETH-USD': {'liq_px': 122838.1600, 'last_px': 0, 'direction': 'sell', 'ts': '2025-04-08 11:03:02'}}

            if self.username in ['falconpat']:

                self.exchanges['deribit'] = {'BTC-USD': {'liq_px':62420, 'last_px': self.latest_prices['BTC-USD']['last_px'], 'direction': 'buy', 'ts': current},'ETH-USD': {'liq_px': 122838.1600, 'last_px': 0, 'direction': 'buy', 'ts': '2025-04-08 11:03:02'}}

                # self.exchanges['htx2'] = {'BTC-USD': {'liq_px':112000, 'last_px': self.latest_prices['BTC-USD']['last_px'], 'direction': 'sell', 'ts': current},'ETH-USD': {'liq_px': 122838.1600, 'last_px': 0, 'direction': 'sell', 'ts': '2025-04-08 11:03:02'}}
            
                # self.exchanges['okx'] = {'BTC-USD': {'liq_px':105000, 'last_px': self.latest_prices['BTC-USD']['last_px'], 'direction': 'buy', 'ts': '2025-04-07 14:01:02'},'ETH-USD': {'liq_px': 122838.1600, 'last_px': 0, 'direction': 'sell', 'ts': '2025-04-08 11:03:02'}}


                # ts has to be the latest to update also because this is the laslt price
                # self.exchanges['deribit'] = {'BTC-USD': {'liq_px': '55000', 'last_px': '60000', 'direction': 'buy', 'ts': '2025-04-18 17:01:02'},'ETH-USD': {'liq_px': 1600, 'last_px': 0, 'direction': 'sell', 'ts': '2025-04-08 11:03:02'}}

            # if self.x %2:
            #     self.exchanges['deribit'] = {'BTC-USD': {'liq_px': 122838.4771710599, 'last_px': self.latest_prices['BTC-USD']['last_px'], 'direction': 'sell', 'ts': '2025-04-07 14:01:02'},'ETH-USD': {'liq_px': 122838.1600, 'last_px': 0, 'direction': 'sell', 'ts': '2025-04-08 11:03:02'}}
            # else:
            #     self.exchanges['deribit'] = {'BTC-USD': {'liq_px': 122838.4771710599, 'last_px': 120000, 'direction': 'sell', 'ts': '2025-04-07 14:01:02'}}
            # self.x += 1

            result = self.check_liq_px_distance(self.exchanges,self.liq_alert_threshold)

            # print(result)
            time.sleep(update_interval)

    def start_background_update(self):
        # Create a new thread to run `update_liq_px` in the background
        update_thread = threading.Thread(target=self.update_liq_px)
        self.update_thread_status = True
        update_thread.daemon = True  # Allows the thread to exit when the main program finishes
        update_thread.start()

   
    def make_call(self,exchange,direction,liq_px,last_px):
        """Initiates a call to the user's phone."""
        call = self.client.calls.create(
            to=self.YOUR_PHONE,
            from_=self.TWILIO_PHONE,
            url="https://handler.twilio.com/twiml/EH2940b91a251c76dd1d2d52e83a4ff983"
        )
        # ADDING SMS
        self.client.messages.create(
            body=(
                f"[LIQUIDATION WARNING! - {exchange.upper()}]\n"
                f"Username: {self.username}\n"
                f"Direction: {direction.upper()}\n"
                f"Remedy: {'Cover short' if direction.upper() == 'SELL' else 'Cover long' }\n"
                f"Liqn Price: {liq_px}\n"
                f"Last Price: {last_px}"
            ),
            from_=self.TWILIO_PHONE,
            to=self.YOUR_PHONE
        )
        return call.sid

    def check_call_status(self, call_sid):
        """Checks the status of the call."""
        call = self.client.calls(call_sid).fetch()
        return call.status  # Possible values: queued, ringing, in-progress, completed, busy, failed, no-answer

    def start_call(self,exchange,direction,liq_px,last_px):
        """Constantly listens for answered status and triggers calls when needed."""
        if self._state & 0b10 :
        
            if self._state== 0b10: # ACTIVE_UNACKED
                alert_status = self.start_alert(exchange,direction,liq_px,last_px)
                print(f"Alert active - {self.STATES[self._state]} {exchange} {direction}: {alert_status}")
                
            
            time.sleep(10)  # Reduced CPU usage
            
        print(f"Monitoring ended - Final state: {self.STATES[self._state]}")
        return 

    def start_alert(self,exchange,direction,liq_px,last_px):
        """Calls once and retries only if there's no response."""
        call_sid = self.make_call(exchange,direction,liq_px,last_px)
        status = self.check_call_status(call_sid)
        while status not in ["in-progress", "completed","busy","no-answer"]:
            # while stats is in queue or ringing , we check the call status
            status = self.check_call_status(call_sid)
            logger.info(f"self.username|{status}")
        # once call is in progress or completed we return False
        time.sleep(5)
        return False

    def stop(self):
        """Stops the background thread."""
        self.running = False



class TraderNotifierFactory:
    def __init__(self):
        self.traders_notifier = {}

    def get_all_trader_notifier(self):
        return self.traders_notifier

    def add_trader_and_notifier(self,username,trader_notifier):
        self.traders_notifier[username] = trader_notifier

    def get_trader_notifier(self,username):
        return self.traders_notifier[username]
        
# INITIALISE FACTORY AND NOTIFIER
cursor = con.cursor()
cursor.execute("""select
                traders.username,
                traders.phone_number,
                MAX(CASE WHEN exchange = 'htx' THEN apikey END) AS htx_apikey,
                MAX(CASE WHEN exchange = 'htx' THEN secretkey END) AS htx_secretkey,
                MAX(CASE WHEN exchange = 'okx' THEN apikey END) AS okx_apikey,
                MAX(CASE WHEN exchange = 'okx' THEN secretkey END) AS okx_secretkey,
                MAX(CASE WHEN exchange = 'okx' THEN passphrase END) AS okx_passphrase
                FROM traders left join api_credentials ac on traders.username = ac.username  group by traders.username,traders.phone_number """)
accounts = cursor.fetchall()
trader_notifier_factory = TraderNotifierFactory()

for account in accounts:
    # TraderNotifier(username, ACCOUNT_SID, AUTH_TOKEN, TWILIO_PHONE, YOUR_PHONE,HTX_APIKEY,HTX_SECRETKEY,OKX_APIKEY,OKX_SECRETKEY,OKX_PASSPHRASE)
    trader_notifier = TraderNotifier(account[0],ACCOUNT_SID, AUTH_TOKEN, TWILIO_PHONE, account[1],account[2],account[3],account[4],account[5],account[6])
    trader_notifier.start_background_update()
    trader_notifier_factory.add_trader_and_notifier(account[0],trader_notifier)
    
app = Flask(__name__)

CORS(app)
@app.route('/change_twilio_alert_running_status', methods=['POST'])
def change_running_status():
    username = request.form.get('username')
    status = request.form.get('status')
    print(username,status,type(username),type(status))
    trader_notifier_factory.get_trader_notifier(username).running = status
    if status:
        print(status, trader_notifier_factory.get_trader_notifier(username).running)
    print(trader_notifier_factory.get_trader_notifier(username).running)
    return "Running status changed", 200

@app.route('/change_twilio_call_answered_status', methods=['POST'])
def change_answered_call_status():
    username = request.form.get('username')
    status = request.form.get('status')

    if trader_notifier_factory.get_trader_notifier(username)._state == 0b10:
        trader_notifier_factory.get_trader_notifier(username)._state = 0b11
        

        return {
            "status": trader_notifier_factory.get_trader_notifier(username)._state,
            "timestamp": datetime.now()
            },200

    return "Alert status change fail", 400


@app.route('/check_alert_status', methods=['POST'])
def check_alert_status():
    username = request.form.get('username')
    trader_notifier = trader_notifier_factory.get_trader_notifier(username)
    state = trader_notifier.STATES[trader_notifier._state]
    # running_status = trader_notifier.running
    print(state)
    return {
            "status": state,
            "timestamp": datetime.now()
            },200

if __name__ == "__main__":

    app.run(port='9000',host ='0.0.0.0')
