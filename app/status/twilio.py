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
        self.answered = False
        self.running = False 
        self.start_call()
        self.get_htx_liq_px_status = True
        self.get_okx_liq_px_status = True
        self.exchanges = {}

        self.liq_alert_threshold = 0.10
        self.update_thread = None
        self.update_thread_status = False

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
                    # print(positions)
                    position_data = next(iter(positions.get('data', [])), {})
                    if 'liq_px' and 'last_price' in position_data:
                        contract = position_data.get('contract_code', '')
                        htx_liq_prices[contract_code] = {"liq_px":position_data['liq_px'],"last_px":position_data['last_price'],"direction":position_data['direction'],"ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(positions['ts'] / 1000))}
                        # if alert:
                        #     self.running = True
                        #     self.start_call()
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
            if symbol in data and isinstance(data[symbol], dict):
                try:
                    liq_px = float(data[symbol]['liq_px'])
                    last_px = float(data[symbol]['last_px'])
                    direction = data[symbol]['direction'] 

                    if direction == 'sell':
                        alert_px = liq_px * (1-threshold)
                        if alert_px <= last_px:
                            print(f"CALLLLLLLLLLL THE TRADER - its {exchange} with {alert_px}|{last_px}")
                            self.running = True 
                    else:
                        alert_px = liq_px * (1+threshold)
                        if alert_px >= last_px:
                            print(f"CALLLLLLLLLLL THE TRADER - its {exchange} with {alert_px}|{last_px}")
                            self.running = True

                    if self.running:
                        self.start_call()            
                 
                except (KeyError, TypeError, ValueError) as e:
                    results[exchange] = {"error": f"Invalid data format: {e}"}
        return results

    def update_liq_px(self,update_interval = 10):
        while self.update_thread_status:
            htx_liq_prices = self.get_htx_liq_px()
            okx_liq_prices = self.get_okx_liq_px()
            print(htx_liq_prices,okx_liq_prices,self.running, self.answered)
            result = self.check_liq_px_distance(self.exchanges,self.liq_alert_threshold)
            
            time.sleep(update_interval)

    def start_background_update(self):
        # Create a new thread to run `update_liq_px` in the background
        update_thread = threading.Thread(target=self.update_liq_px)
        self.update_thread_status = True
        update_thread.daemon = True  # Allows the thread to exit when the main program finishes
        update_thread.start()

   
    def make_call(self):
        """Initiates a call to the user's phone."""
        call = self.client.calls.create(
            to=self.YOUR_PHONE,
            from_=self.TWILIO_PHONE,
            url="https://handler.twilio.com/twiml/EH2940b91a251c76dd1d2d52e83a4ff983"
        )
        return call.sid

    def check_call_status(self, call_sid):
        """Checks the status of the call."""
        call = self.client.calls(call_sid).fetch()
        return call.status  # Possible values: queued, ringing, in-progress, completed, busy, failed, no-answer

    def start_call(self):
        """Constantly listens for answered status and triggers calls when needed."""
        while self.running:
            if not self.answered:  # Only start alert if not answered
                alert_status = self.start_alert()
                print(alert_status)
            time.sleep(5)  # Avoids excessive CPU usage
        self.answered= False
        return False

    def start_alert(self):
        """Calls once and retries only if there's no response."""
        call_sid = self.make_call()
        # print(f"Calling... Call SID: {call_sid}")
        status = self.check_call_status(call_sid)
        # print(f"Call FIRST Status: {status}")
        while status not in ["in-progress", "completed"]:
            # print(self.answered)
            # print(status)
            status = self.check_call_status(call_sid)
        if self.answered:
            self.running = False
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
                FROM traders left join api_credentials ac on traders.username = ac.username where traders.username ='brennan12' group by traders.username,traders.phone_number """)
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
        trader_notifier_factory.get_trader_notifier(username).start_call()
    print(trader_notifier_factory.get_trader_notifier(username).running)
    return "Running status changed", 200

@app.route('/change_twilio_call_answered_status', methods=['POST'])
def change_answered_call_status():
    username = request.form.get('username')
    status = request.form.get('status')
    print(username,status,type(username),type(status))
    trader_notifier_factory.get_trader_notifier(username).answered = status
    print(trader_notifier_factory.get_trader_notifier(username).answered)
    return "Alert tatus changed", 200


@app.route('/check_alert_status', methods=['POST'])
def check_alert_status():
    username = request.form.get('username')
    # print(username,status,type(username),type(status))
    incident_status =trader_notifier_factory.get_trader_notifier(username).running 
    answer_status = trader_notifier_factory.get_trader_notifier(username).answered
    print(incident_status,answer_status)
    return {"running":f"{incident_status}","answered":f"{answer_status}"}, 200

if __name__ == "__main__":

    app.run(port='9000',host ='0.0.0.0')
