from flask import Flask, jsonify, request
from datetime import datetime
import psycopg2
import psycopg2.extras

from pathlib import Path

# Logger 
# Define the log directory and the log file name
LOG_DIR = Path('/var/www/html/orderbook/logs')
log_filename = LOG_DIR / (Path(__file__).stem + '.log')
import os
os.makedirs(LOG_DIR, exist_ok=True)
# Set up basic logging configuration
import logging
file_handler = logging.FileHandler(log_filename)
# Set up a basic formatter

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger = logging.getLogger('Diaoyu')
logger.setLevel(logging.INFO)  # Set log level
# Add the file handler to the logger
logger.addHandler(file_handler)

import configparser
import os
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
config.read(config_file_path)

# config_source = 'localdb'
config_source = config['dbchoice']['db']
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
from app.strategies.redis_pubsub import RedisPublisher


import threading
import multiprocessing
import time
import random


class Algo:
    """Represents an algorithm instance."""
    def __init__(self, algo_id, config):
        self.algo_id = algo_id
        self.config = config

    def execute(self):
        """Execute the algorithm logic."""
        print(f"Executing Algo {self.algo_id} with config: {self.config}")
        time.sleep(random.uniform(0.5, 2))  # Simulate work

class AlgoFactory:
    """Manages Algo instances and listens for updates."""
    def __init__(self):
        self.algos = {}
        self.lock = threading.Lock()
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.manager = multiprocessing.Manager()
        self.shared_states = {}

    def add_or_update_algo(self, instance_id, algo_details):
        """Add a new strategy or update an existing one."""
        if instance_id in self.algos:
            logger.debug(algo_details)
            # Update existing strategy
            shared_state = self.shared_states[instance_id]
            #  {'username': 'brennan_st', 'algo_type': 'diaoyu', 'algo_name': 'test1', 'lead_exchange': 'okx', 'lag_exchange': 'htx', 'spread': '200', 'qty': '1', 'ccy': 'BTC-USD-SWAP', 'instrument': 'swap', 'contract_type': 'thisweek', 'state': True, 'htx_apikey': 'e045967e-fbbc0636-e6d030e1-bewr5drtmh', 'htx_secretkey': '7d4bac9e-780e3558-de6db8f8-5a0df', 'okx_apikey': 'a0de3940-5679-4939-957a-51c87a8502d9', 'okx_secretkey': 'FA44BCAAC3788C2AB4AFC77047930792', 'okx_passphrase': 'falconstead@Trading2024', 'order_id': 1328717969429176320}
#             algo_details
#  {'operation': 'UPDATE', 'data': {'id': 143, 'username': 'brennan_st', 'algo_type': 'diaoyu', 'algo_name': 'test1234', 'lead_exchange': 'okx', 'lag_exchange': 'htx', 'spread': '5000', 'qty': '1', 'ccy': 'BTC-USD-SWAP', 'instrument': 'swap', 'contract_type': 'thisweek', 'state': True, 'updated_at': '2025-01-14T14:51:04.940568'}}
            json_data = algo_details.get('data','')
            self.shared_states[instance_id]['lead_exchange'] = json_data['lead_exchange']
            self.shared_states[instance_id]['lag_exchange'] = json_data['lag_exchange']
            self.shared_states[instance_id]['spread'] = json_data['lead_exchange']
            self.shared_states[instance_id]['qty'] = json_data['qty']
            self.shared_states[instance_id]['ccy'] = json_data['ccy']
            self.shared_states[instance_id]['instrument'] = json_data['instrument']
            self.shared_states[instance_id]['contract_type'] = json_data['contract_type']
            self.shared_states[instance_id]['state'] =  json_data['state']
            # self.factory.shared_states[instance_id]['htx_apikey'] = json_data['contract_type']
            # self.factory.shared_states[instance_id]['htx_secretkey'] = json_data['contract_type']
            # self.factory.shared_states[instance_id]['okx_apikey'] = json_data['contract_type']
            # self.factory.shared_states[instance_id]['okx_secretkey'] = json_data['contract_type']
            # self.factory.shared_states[instance_id]['okx_passphrase'] = json_data['contract_type']
            # self.factory.shared_states[instance_id]['order_id'] = json_data['contract_type']


            strat_and_process = self.algos.get(instance_id)
            strat = strat_and_process[0]
            logger.debug('algofactory updating state',self.shared_states[instance_id]['state'] )
            
         

            logger.debug(f"Updated strategy {instance_id} with new details.")
        else:
            # Add a new strategy
            logger.debug(f"Adding new strategy {instance_id}...")
            
            # Create a shared state dictionary
            shared_state = self.manager.dict(algo_details['data'])
            
            # Create the new strategy instance (Diaoyu)
            strat = Diaoyu(shared_state, self.conn.cursor())
            
            # Create a new process for the strategy
            process = multiprocessing.Process(target=strat.start_clients)
            
            # Store the strategy and process in the `algos` dictionary
            self.algos[instance_id] = (strat, process)
            
            # Store the shared state for the instance
            self.shared_states[instance_id] = shared_state
            
            # Start the process
            process.start()

            logger.debug(f"Added new strategy {instance_id} and started process.")


    def remove_algo(self, algo_id):
        """Remove an Algo instance."""
        with self.lock:
            if algo_id in self.algos:
                print(f"Removing Algo {algo_id}")
                del self.algos[algo_id]

    def get_algo(self, algo_id):
        """Get an Algo instance."""
        with self.lock:
            return self.algos.get(algo_id)

    
    def execute_all(self):
        """Execute all algorithms in parallel using multiprocessing."""
        processes = []
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
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
            row_dict = {}
            
            row_dict['username'] =  row[0]
            row_dict['algo_type'] = row[1]
            row_dict['algo_name'] = row[2]
            row_dict['lead_exchange'] = row[3]
            row_dict['lag_exchange'] = row[4]
            row_dict['spread']= row[5]
            row_dict['qty'] = row[6]
            row_dict['ccy'] = row[7]
            row_dict['instrument'] = row[8]
            row_dict['contract_type'] = row[9]
            row_dict['state'] = row[10]
            row_dict['htx_apikey'] = row[11]
            row_dict['htx_secretkey'] = row[12]
            row_dict['okx_apikey'] = row[13]
            row_dict['okx_secretkey'] = row[14]
            row_dict['okx_passphrase'] = row[15]
            
            # Create a unique instance ID
            instance_id = f"{row_dict['username']}_{row_dict['algo_type']}_{row_dict['algo_name']}"
            # print(f"Instance ID: {instance_id}")
            logger.debug(instance_id)
            key,jwt_token = '',''
            # Initialize the strategy
            # Since Diaoyu is trading SWAP, we will keep contract type as None
            self.shared_states[instance_id] = self.manager.dict(row_dict)

            strat = Diaoyu(self.shared_states[instance_id],self.conn.cursor())
            p = multiprocessing.Process(target=strat.start_clients)
            self.algos[instance_id] = (strat, p)  # Update with the new process
            p.start()



class DBListener(threading.Thread):
    """Simulates a database listener."""
    def __init__(self, factory):
        super().__init__()
        self.running = True
        self.factory = factory
        self.conn = psycopg2.connect(**DB_CONFIG)
        

    def run(self):
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = self.conn.cursor()
        cur.execute("LISTEN algo_dets_channel;")

        """Continuously listen for database updates."""
        while self.running:
            # Simulate database update events
            # event = random.choice(["create", "update", "delete"])
            self.conn.poll()
            while self.conn.notifies:
                notify = self.conn.notifies.pop()
                algo_details = json.loads(notify.payload)
                json_data = algo_details['data']
                operation = algo_details['operation'] # db operations: update,insert...
            
                # Initialize and start new AlgoRunTime instance
                username = json_data['username']
                algo_type = json_data['algo_type']
                algo_name = json_data['algo_name']
                instance_id = f"{username}_{algo_type}_{algo_name}"
                if operation == "INSERT":
                    cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                    # cur.execute("select * from algo_dets")
                    cur.execute(f"""select
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
                        FROM algo_dets ad left join api_credentials ac on ad.username = ac.username where ad.username= '{username}' and ad.algo_type ='{algo_type}' and algo_name='{algo_name}' group by ad.username,ad.algo_type,ad.algo_name,ad.lead_exchange,ad.lag_exchange,ad.spread,ad.qty,ad.ccy,ad.instrument,ad.contract_type,ad.state"""
                    )
                    new_algo_detail = cur.fetchone()
                    self.factory.add_or_update_algo(algo_details)


                    #
                # For updates
                elif operation == 'UPDATE':
                    # self.factory.shared_states[instance_id] = algo_details
                    logger.debug(self.factory.shared_states)
                    logger.debug('UPDATE')
                    logger.debug(self.factory.shared_states[instance_id])
                    # self.factory.shared_states[instance_id]['state'] = True
                    self.factory.add_or_update_algo(instance_id,algo_details)
                    logger.debug(self.factory.shared_states[instance_id])

                else:
                    self.factory.remove_algo(instance_id)
     

    def stop(self):
        """Stop the listener."""
        self.running = False


if __name__ == "__main__":
    # Instantiate AlgoFactory
    factory = AlgoFactory()

    # Start the DB listener in a separate thread
    db_listener = DBListener(factory)
    db_listener.start()

    try:
        # while True:
        #     # Periodically execute all algorithms
        print("Executing all algorithms...")
        factory.execute_all()
            # time.sleep(5)
    except KeyboardInterrupt:
        print("Shutting down...")
        db_listener.stop()
        db_listener.join()
