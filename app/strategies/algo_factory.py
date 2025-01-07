from flask import Flask, jsonify, request
from datetime import datetime
import psycopg2
import psycopg2.extras
import configparser
import os
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
config.read(config_file_path)

config_source = 'localdb'
dbusername = config[config_source]['username']
dbpassword = config[config_source]['password']
dbname = config[config_source]['dbname']

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    "dbname": dbname,
    "user": dbusername,
    "password": dbpassword,
    "host": "localhost",
    "port": 5432
}

from app.strategies.diaoyu import Diaoyu
import time
import json
import select

class DatabaseNotificationListener:
    def __init__(self, db_config, channel, filter_username=None, filter_algoname= None, callback = None):
        """
        Initialize the DatabaseNotificationListener.

        :param config_file: Path to the configuration file.
        :param config_source: The section name in the configuration file.
        :param channel: The PostgreSQL notification channel to listen to.
        :param filter_username: Optional username to filter notifications by.
        """
        self.channel = channel
        self.filter_username = filter_username
        self.filter_algoname = filter_algoname
        self.db_config = db_config
        self.callback = callback

    def listen(self):
        """
        Start listening for PostgreSQL notifications on the specified channel.
        """
        try:
            # Connect to the PostgreSQL database
            conn = psycopg2.connect(
                                    dbname=self.db_config['database'],
                                    user=self.db_config['user'],
                                    password=self.db_config['password'],
                                    host=self.db_config['host'],
                                    port=self.db_config['port']
                                    )
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()

            # Start listening to the channel
            cur.execute(f"LISTEN {self.channel};")
            print(f"Listening for notifications on '{self.channel}'...")

            while True:
                # Wait for a notification with a timeout
                if select.select([conn], [], [], 5) == ([], [], []):
                    print("No notification received within 5 seconds.")
                    continue
                
                # Poll the connection for notifications
                conn.poll()
                while conn.notifies:
                    notify = conn.notifies.pop()
                    self._process_notification(notify)

        except Exception as e:
            print(f"Error listening for notifications: {e}")
            time.sleep(5)  # Retry delay
            self.listen()  # Retry listening

    def _process_notification(self, notify):
        """
        Process a received PostgreSQL notification.
        :param notify: The notification object.
        """
        try:
            # Parse the payload as JSON
            payload = json.loads(notify.payload)
            operation = payload.get('operation')
            data = payload.get('data')
            username = self.filter_username
            algoname = self.filter_algoname
            self.callback(payload)

            # Check if the username matches the filter
            if self.filter_username is None or username :
                print(
                    f"Notification received for user '{username}': {operation} - {data}"
                )
            else:
                print(f"Ignored notification for user '{username}'.")

        except json.JSONDecodeError:
            print(f"Received invalid JSON payload: {notify.payload}")

class AlgoRunTime:
    def __init__(self, instance_id):
        self.instance_id = instance_id
        # self.api_url = api_url
        self.running = False

    def start(self):
        self.running = True
        print(f"Instance {self.instance_id} started.")
        self.run_application()

    def run_application(self):
        try:
            # Simulate long-running process
            for _ in range(5):  # Example loop, replace with actual logic
                print(f"Instance {self.instance_id} is running...")
                time.sleep(200)

            # Simulate condition met, application stopping
            self.stop("Condition met for stopping.")

        except Exception as e:
            self.stop(f"Application stopped due to error: {e}")

    def stop(self, reason):
        self.running = False
        print(f"Instance {self.instance_id} stopped. Reason: {reason}")

 


class AlgoFactory:
    def __init__(self,instance_id=None, algo_instance = None):
        self.algo_instance_list = {instance_id:algo_instance} if algo_instance is not None else {}

    def addToDict(self,instance_id,algo_instance):
        self.algo_instance_list[instance_id] =(algo_instance)

    def removeFromDict(self,instance_id,algo_instance):
        self.algo_instance_list[instance_id] = None 

    
import threading

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def run_all_algo():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # cur.execute("select * from algo_dets")
    cur.execute("""select
        ad.username,
        ad.algo_type,
        ad.algo_name,
        ad.lead_exchange,
        ad.lag_exchange ,
        ad.spread,
        ad.qty,
        ad.ccy,
        ad.instrument,
        ad.contract_type,
        ad.state,
        MAX(CASE WHEN exchange = 'htx' THEN apikey END) AS htx_apikey,
        MAX(CASE WHEN exchange = 'htx' THEN secretkey END) AS htx_secretkey,
        MAX(CASE WHEN exchange = 'okx' THEN apikey END) AS okx_apikey,
        MAX(CASE WHEN exchange = 'okx' THEN secretkey END) AS okx_secretkey,
        MAX(CASE WHEN exchange = 'okx' THEN passphrase END) AS okx_passphrase   
        FROM algo_dets ad left join api_credentials ac on ad.username = ac.username  group by ad.username,ad.algo_type,ad.algo_name,ad.lead_exchange,ad.lag_exchange,ad.spread,ad.qty,ad.ccy,ad.instrument,ad.contract_type,ad.state"""
    )
    algo_details = cur.fetchall()
    for row in algo_details:
        # Initialize class and start AlgoRunTime
        print('Running row:', row)
        username =  row[0]
        algo_type = row[1]
        algo_name = row[2]
        lead_exchange = row[3]
        lag_exchange = row[4]
        spread = row[5]
        qty = row[6]
        ccy = row[7]
        instrument = row[8]
        contract_type = row[9]
        state = row[10]
        htx_apikey = row[11]
        htx_secretkey = row[12]
        okx_apikey = row[13]
        okx_secretkey = row[14]
        okx_passphrase = row[15]

        # Create a unique instance ID
        instance_id = f"{username}_{algo_type}_{algo_name}"
        # print(f"Instance ID: {instance_id}")
        
        key,jwt_token = '',''
        # Initialize the strategy
        # Since Diaoyu is trading SWAP, we will keep contract type as None
        strat = Diaoyu(
            username, key, jwt_token, htx_apikey, htx_secretkey,okx_apikey, okx_secretkey, okx_passphrase, algo_name, qty, ccy, spread,
            lead_exchange, lag_exchange, state, instrument, contract_type=None
        )
        # Start the strategy in a new thread
        thread = threading.Thread(target=strat.start_clients, daemon=True)
        thread.start()
        
        # Add the strategy instance to the factory
        algo_factory.addToDict(instance_id, strat)
        
        # print(f"Currently running instances: {list(algo_factory.algo_instance_list.keys())}")

    time.sleep(1000)

async def run_thread(strat):
    threading.Thread(target=strat.start_clients()).start()


def listen_for_updates():
    print('listneing')

    conn = get_db_connection()
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute("LISTEN algo_dets_channel;")
    print("Listening for updates on algo_dets...")

    while True:
        conn.poll()
        while conn.notifies:
            notify = conn.notifies.pop()
            # print(f"Received notification: {notify.payload}")
            algo_details = json.loads(notify.payload)
            json_data = algo_details['data']
            operation = algo_details['operation']
            # print(algo_details)
            # print(operation)
            # Initialize and start new AlgoRunTime instance
            instance_id = f"{json_data['username']}_{json_data['algo_type']}_{json_data['algo_name']}"
            print(algo_factory.algo_instance_list)
            # For new strategies being inserted
            if operation == "INSERT":
                algo_runtime = Diaoyu(instance_id)
                threading.Thread(target=algo_runtime.start).start()
                algo_factory.addToDict(instance_id,AlgoRunTime)
                # print(algo_factory.algo_instance_list)
            # For updates
            else:
                algo_instance = algo_factory.algo_instance_list[instance_id]
                # print("ALGO INSTANCE",algo_instance)
                # print(json_data)
                algo_instance.update_with_notification(algo_details)

# Require one script that assumes we start from 0 algos and another script to refresh the algo 

if __name__ == "__main__":
    # algo_factory = AlgoFactory()
    algo_factory = AlgoFactory()
    threading.Thread(target=listen_for_updates, daemon=True).start()
    run_all_algo()  # Start existing instances


    
