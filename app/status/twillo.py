from twilio.rest import Client
import time
import os
from twilio.twiml.voice_response import VoiceResponse
import asyncio
import threading
# Run the alert function
import datetime
import pg8000
from pg8000.dbapi import ProgrammingError, DatabaseError
from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS
import traceback
import configparser
from orderbook.app.htx2.HtxOrderClass import HuobiCoinFutureRestTradeAPI

config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '../orderbook', 'config_folder', 'credentials.ini')
print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)
app = Flask(__name__)
CORS(app)
config_source = config['dbchoice']['db']
dbusername = config[config_source]['username']
dbpassword = config[config_source]['password']
dbname = config[config_source]['dbname']
app = Flask(__name__)
CORS(app)
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
        self.htx_last_px = None
        self.htx_liq_px = None
        self.okx_liq_px = None
        self.get_htx_liq_px_status = True
        self.htx_liq_alert_threshold = 0.15
        self.get_htx_liq_px()
        self.htx_liq_alert = (self.htx_last_px == self.htx_liq_px*(1-self.htx_liq_alert_threshold)) if self.htx_last_px and self.htx_liq_px else None
        
        
    def get_htx_liq_px(self):
        try:
            if self.get_htx_liq_px_status:
                print('hello')
                
                # Data received from the client (assuming JSON body)
                instId = "BTC-USD"
                instId_list = ["BTC-USD"]
                tdMode = "cross"

                # Extract necessary parameters from the request
                tradeApi = HuobiCoinFutureRestTradeAPI(
                    "https://api.hbdm.com",
                    self.htx_apikey,
                    self.htx_secretkey
                )

                ccy_liq_px = {}

                for contract_code in instId_list:
                    positions = asyncio.run(tradeApi.get_positions(instId, body={"contract_code": contract_code}))
                    # Use next() to safely get the first element or default to an empty dict
                    # print(positions)
                    position_data = next(iter(positions.get('data', [])), {})
                    if 'liq_px' and 'last_price' in position_data:
                        contract = position_data.get('contract_code', '')
                        self.htx_liq_px = position_data['liq_px']
                        self.htx_last_px = position_data['last_price']
                        ccy_liq_px[contract] = position_data['liq_px']  # Add if missing, replace if exists
                        
                        alert = self.htx_last_px <= self.htx_liq_px*(1 - self.htx_liq_alert_threshold)
                        print(self.htx_liq_px*(1 - self.htx_liq_alert_threshold), self.htx_last_px,alert)

                        if alert:
                            self.running = True
                            self.start_call()
                
                return position_data

        except Exception as e:
            print(f"ERROR {traceback.format_exc()}")
  



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

app = Flask(__name__)
@app.route('/change_twilio_alert_running_status', methods=['POST'])
def change_running_status():
    username = request.form.get('username')
    status = request.form.get('status')
    print(username,status,type(username),type(status))
    trader_notifier_factory.get_trader_notifier(trader[0]).running = status

    if status:
        
        trader_notifier_factory.get_trader_notifier(trader[0]).start_call()
    print(trader_notifier_factory.get_trader_notifier(username).running)
    return '200'

@app.route('/change_twilio_call_answered_status', methods=['POST'])
def change_answered_call_status():
    username = request.form.get('username')
    status = request.form.get('status')
    print(username,status,type(username),type(status))
    trader_notifier_factory.get_trader_notifier(trader[0]).answered = status
    print(trader_notifier_factory.get_trader_notifier(username).answered)
    return '200'

if __name__ == "__main__":
    # Create cursor object to execute queries

    cursor = con.cursor()

    # cursor.execute("SELECT trader_name,phone_number from traders")
    # traders = cursor.fetchall()
    # trader_notifier_factory = TraderNotifierFactory()
    # for trader in traders:
    #     trader_notifier = TraderNotifier(trader[0],ACCOUNT_SID, AUTH_TOKEN, TWILIO_PHONE, trader[1],htx_apikey,htx_secretkey,okx_apikey,okx_secretkey)
    #     trader_notifier_factory.add_trader_and_notifier(trader[0],trader_notifier)

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
        trader_notifier_factory.add_trader_and_notifier(account[0],trader_notifier)
    print(trader_notifier_factory.get_trader_notifier('brennan12').running)

    app.run(port='9000')
