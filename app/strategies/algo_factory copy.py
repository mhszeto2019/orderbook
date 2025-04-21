from flask import Flask, jsonify, request
from datetime import datetime
import psycopg2
import psycopg2.extras
import sys
from pathlib import Path
from collections import defaultdict
import psutil
import asyncio
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
logger = logging.getLogger('Algo_factory')
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

from app.htx2.HtxOrderClass import HuobiCoinFutureRestTradeAPI

from app.strategies.diaoyu import Diaoyu
from app.strategies.diaoxia import Diaoxia
import time
import json
import select
from app.strategies.redis_pubsub import RedisPublisher


import threading
import multiprocessing
import time
import random


# from flask import Flask, request, jsonify
# import threading
# import time
# import os
# import signal

# app = Flask(__name__)

# # Global variable to track if the task is running
# task_thread = None
# shutdown_flag = False

# # Background function
# def background_task():
#     # Instantiate AlgoFactory
#     factory = AlgoFactory()

#     # Start the DB listener in a separate thread
#     db_listener = DBListener(factory)
#     db_listener.start()
#     try:
#         # while True:
#         #     # Periodically execute all algorithms
#         # print("Executing all algorithms...")
#         factory.execute_all()
#             # time.sleep(5)
#     except KeyboardInterrupt:
#         logger.error("KeyboardInterrupt detected. Shutting down gracefully...")
#         # print("KeyboardInterrupt detected. Shutting down gracefully...")
#     except Exception as e:
#         logger.error(f"Error detected: {e}")
#         # print(f"An unexpected error occurred: {e}")
#     finally:
#         # Ensure cleanup happens no matter what
#         # print("Cleaning up...")
#         factory.stop_all()
#         db_listener.stop()
#         factory.handle_termination_signal(None,None)
#         db_listener.join()

# # Start the task
# @app.route('/start', methods=['POST'])
# def start():
#     global task_thread, shutdown_flag
#     if task_thread and task_thread.is_alive():
#         return jsonify({"message": "Task is already running"}), 400

#     shutdown_flag = False
#     task_thread = threading.Thread(target=background_task)
#     task_thread.start()

#     return jsonify({"message": "Task started"}), 200

# # Stop the task and Flask server
# @app.route('/shutdown', methods=['POST'])
# def shutdown():
#     global shutdown_flag
#     shutdown_flag = True
#     os.kill(os.getpid(), signal.SIGINT)  # Kill the process
#     return jsonify({"message": "Shutting down server"}), 200

# # Check if task is running
# @app.route('/status', methods=['GET'])
# def status():
#     global task_thread
#     return jsonify({"running": task_thread.is_alive() if task_thread else False}), 200


class AlgoFactory:
    """Manages Algo instances and listens for updates."""
    def __init__(self):
        self.algos = {}
        self.lock = threading.Lock()
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.manager = multiprocessing.Manager()
        self.shared_states = {}
        self.processes = []
        self.queue = multiprocessing.Manager().Queue()
        self.user_algo_type_count = {}

     
        


    def initialise_strat(self,algo_type,instance_id,db_cursor):
        if algo_type == 'diaoyu':
            strat = Diaoyu(self.shared_states[instance_id],db_cursor)
            # Create a new process for the strategy

        elif algo_type == 'diaoxia':
            strat = Diaoxia(self.shared_states[instance_id], db_cursor)

            # Create a new process for the strategy
        process = multiprocessing.Process(target=strat.start_clients)
        # Store the strategy and process in the `algos` dictionary
        self.algos[instance_id] = (strat, process)
        # Store the shared state for the instance
        self.shared_states[instance_id]['pname'] = process._name
        
        # Start the process
        process.start()
        self.processes.append(process)


    def update_user_algo_type_count(self, username: str, algotype: str, spread: int, qty: int):
        """Updates buy/sell counts for a user's algorithm type."""  
        if algotype == 'diaoyu':
            side = 'buy' if spread > 0 else 'sell'
        elif algotype == 'diaoxia':
            # if spread is negative, it sells on okx buy on htx
            side = 'sell' if spread > 0 else 'buy'
        # Safely update buy/sell count
        
        if self.user_algo_type_count[username][algotype][side]  < 0:
            self.user_algo_type_count[username][algotype][side] = 0 
        self.user_algo_type_count[username][algotype][side] += qty 

    def reset_algo_count(self,username,algotype, algoname):
        # self.user_algo_type_count[username][algotype][algoname] = {
        #     'buy': 0,
        #     'sell': 0,
        #     'filled_amount': 0,
        #     'remaining_amount': 0,
        #     'average_fill_price': 0.0,
        #     'total_executed_value': 0.0,
        #     'max_position_limit': 100,
        #     'start_time': None,
        #     'end_time': None,
        #     'execution_log': [],
        #     'error_log': [],
        #     'status': False
        # }
        
        
        self.user_algo_type_count[username][algotype][algoname]['filled_amount'] = 0
        self.user_algo_type_count[username][algotype][algoname]['remaining_amount'] = self.user_algo_type_count[username][algotype][algoname]['buy'] if self.user_algo_type_count[username][algotype][algoname]['buy'] else self.user_algo_type_count[username][algotype][algoname]['sell']
        self.user_algo_type_count[username][algotype][algoname]['total_executed_value'] = 0.0
        self.user_algo_type_count[username][algotype][algoname]['start_time'] = None
        self.user_algo_type_count[username][algotype][algoname]['end_time'] = None
        self.user_algo_type_count[username][algotype][algoname]['execution_log'] = []
        self.user_algo_type_count[username][algotype][algoname]['error_log'] = []
        self.user_algo_type_count[username][algotype][algoname]['status'] =False

        







    def update_algo(self, instance_id, algo_details):
        
        # Update existing strategy
        # shared_state = self.shared_states[instance_id]
        logger.debug('UPDATING NEW STRAT')
        json_data = algo_details.get('data','')
        # Update state in multiprocess
        self.shared_states[instance_id]['lead_exchange'] = json_data['lead_exchange']
        self.shared_states[instance_id]['lag_exchange'] = json_data['lag_exchange']
        self.shared_states[instance_id]['spread'] = json_data['spread']
        self.shared_states[instance_id]['qty'] = json_data['qty']
        self.shared_states[instance_id]['ccy'] = json_data['ccy']
        self.shared_states[instance_id]['instrument'] = json_data['instrument']
        self.shared_states[instance_id]['contract_type'] = json_data['contract_type']
        self.shared_states[instance_id]['state'] =  json_data['state']
        # self.shared_states[instance_id]['filled_vol'] = json_data['filled_vol']
        # self.shared_states[instance_id]['filled_qty'] = json_data['filled_qty']

        logger.info(self.shared_states[instance_id]['filled_vol'])

        # strat_and_process = self.algos.get(instance_id)
        # print(strat_and_process)

        # strat = strat_and_process[0]
        # print(f"ALGO DETAILS that just got updated:{algo_details}")
        username,algo_type,algo_name = instance_id.split('_')
        qty = int(json_data['qty']) 
        # filled_vol = self.shared_states[instance_id]['filled_vol']

        print(f"{username} |{algo_type}| json: {json_data['spread']} qty:{qty}")

        # if json_data['state']: #if status is True which means algo is on
        #     self.update_user_algo_type_count(username,algo_type,int(json_data['spread']),qty)
        # else:
        #     self.update_user_algo_type_count(username,algo_type,int(json_data['spread']),-qty)

        if not json_data['state']: #if status is False we reset the algo
            self.reset_algo_count(username,algo_type,algo_name)
        else:
            self.user_algo_type_count[username][algo_type][algo_name]['status'] = True
        logger.info("Updating algo")
        logger.info(self.user_algo_type_count)

        for instance_id in self.shared_states:
            if username in instance_id:
                self.shared_states[instance_id]['user_algo_type_count'] = self.user_algo_type_count

    async def get_positions_async(self,apikey,secretkey):
        positions = await HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",apikey,secretkey).get_positions('BTC',body = {
                    "symbol": "BTC"
                    }
                    )
        logger.info(positions)
        position_data = positions.get('data', []) if positions else []
        # Check if position_data has at least one item to avoid IndexError 
        # If there is a position, we need to find out these conditions:
            #1) limit_size left for our new order which is called availability
            #2) limit size required to close existing opposite direction called closing size
        # If there is position, prioritise on closing first

        logger.info(f"POSITION DATA {position_data}")
        direction = position_data[0]['direction']

        availability = int(position_data[0]['volume']) if direction == 'buy' else -int(position_data[0]['volume'])
    
        logger.info(availability)
        return availability

    def add_algo(self, instance_id, algo_details):
        """Add a new strategy or update an existing one."""
    
        # Add a new strategy
        logger.info(f"Updating strategy {instance_id}...")
        

        # Create a shared state dictionary called row_dict
        row_dict  = {}
        row_dict['username'] =  algo_details[0]
        row_dict['algo_type'] = algo_details[1]
        row_dict['algo_name'] = algo_details[2]
        row_dict['lead_exchange'] = algo_details[3]
        row_dict['lag_exchange'] = algo_details[4]
        row_dict['spread']= algo_details[5]
        row_dict['qty'] = algo_details[6]
        row_dict['ccy'] = algo_details[7]
        row_dict['instrument'] = algo_details[8]
        row_dict['contract_type'] = algo_details[9]
        row_dict['state'] = algo_details[10]    
        # row_dict['trade_direction'] = algo_details[11]
        row_dict['htx_apikey'] = algo_details[11]
        row_dict['htx_secretkey'] = algo_details[12]
        row_dict['okx_apikey'] = algo_details[13]
        row_dict['okx_secretkey'] = algo_details[14]
        row_dict['okx_passphrase'] = algo_details[15]
        row_dict['filled_vol'] = 0
        # row_dict[f'{row_dict['username']}_queue'] = self.queue
        
        instance_id = f"{row_dict['username']}_{row_dict['algo_type']}_{row_dict['algo_name']}"
        positions = asyncio.run(self.get_positions_async(row_dict['htx_apikey'],row_dict['htx_secretkey']))
        # logger.info(positions)
      

        
        # Check if the username exists, if not, initialize it
        if row_dict['username'] not in self.user_algo_type_count:
            self.user_algo_type_count[row_dict['username']] = {'net_availability': positions}

        # Check if the algo_type exists for this username, if not, initialize it
        if row_dict['algo_type'] not in self.user_algo_type_count[row_dict['username']]:
            self.user_algo_type_count[row_dict['username']][row_dict['algo_type']] = {}

        # Check if the algo_name exists for this algorithm type, if not, initialize it
        if row_dict['algo_name'] not in self.user_algo_type_count[row_dict['username']][row_dict['algo_type']]:
            if row_dict['algo_type'] == 'diaoyu':
                buy_amt = int(row_dict['qty']) if int(row_dict['spread']) > 0 else 0
                sell_amt = int(row_dict['qty']) if int(row_dict['spread']) < 0 else 0
            else:
                buy_amt = int(row_dict['qty']) if int(row_dict['spread']) < 0 else 0
                sell_amt = int(row_dict['qty']) if int(row_dict['spread']) > 0 else 0

            self.user_algo_type_count[row_dict['username']][row_dict['algo_type']][row_dict['algo_name']] = {
                'buy': buy_amt,
                'sell': sell_amt,
                'filled_amount': 0,
                'remaining_amount': buy_amt if buy_amt >0 else sell_amt,
                'average_fill_price': 0.0,
                'total_executed_value': 0.0,
                'max_position_limit': 100,
                'start_time': None,
                'end_time': None,
                'execution_log': [],
                'error_log': [],
                'status': False
            }


        row_dict['user_algo_type_count'] = self.user_algo_type_count
        
        logger.info(row_dict['user_algo_type_count'])


        self.shared_states[instance_id] = self.manager.dict(row_dict)
        # Create the new strategy instance (Diaoyu)
    
        logger.debug(f"CREATING NEW STRAT with - {self.shared_states[instance_id]}")
        self.initialise_strat(row_dict['algo_type'],instance_id,psycopg2.connect(**DB_CONFIG).cursor())

        for p in self.processes:
            p.join

    # algo id here is instance id from main class
    def remove_algo(self, algo_id,json_data):
        """Remove an Algo instance."""
        with self.lock:
            logger.debug(f"REMOVE ALGO:{self.user_algo_type_count}")            
            if json_data['algo_type'] == 'diaoyu':
                side = 'buy' if int(json_data['spread']) > 0 else 'sell'
            elif json_data['algo_type'] == 'diaoxia':
                side = 'sell' if int(json_data['spread']) > 0 else 'buy'
            # if not json_data['state']:
            try:
                del self.user_algo_type_count[json_data['username']][json_data['algo_type']][json_data['algo_name']]
                logger.info(f"Algorithm '{json_data['algo_name']}' removed successfully.")
            except KeyError:
                logger.info(f"Algorithm '{json_data['algo_name']}' not found for {json_data['username']} -> {json_data['algo_name']}.")


            if algo_id in self.algos:
                logger.debug(f"Removing Algo {algo_id}")
                del self.algos[algo_id]
                logger.debug(f"Removed algo {algo_id}")

            for p in self.processes:
                if p._name == self.shared_states[algo_id]['pname']:
                    p.terminate()
                    p.join()  # Ensure the process is properly cleaned up
                    self.processes.remove(p)  # Remove from the list if needed
                    break  # Exit after finding and terminating the target process

    def get_algo(self, algo_id):
        """Get an Algo instance."""
        with self.lock:
            return self.algos.get(algo_id)

    def execute_all(self):
        """Execute all algorithms in parallel using multiprocessing."""
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
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
            # row_dict['trade_direction'] = row[11]
            row_dict['htx_apikey'] = row[11]
            row_dict['htx_secretkey'] = row[12]
            row_dict['okx_apikey'] = row[13]
            row_dict['okx_secretkey'] = row[14]
            row_dict['okx_passphrase'] = row[15]
            row_dict['filled_vol'] = 0

            # INITIALISING USER_ALGO_TYPE_COUNT

            positions = asyncio.run(self.get_positions_async(row_dict['htx_apikey'],row_dict['htx_secretkey']))

            logger.info(positions)

            # Check if the username exists, if not, initialize it
            if row_dict['username'] not in self.user_algo_type_count:
                self.user_algo_type_count[row_dict['username']] = {'net_availability': positions}

            # Check if the algo_type exists for this username, if not, initialize it
            if row_dict['algo_type'] not in self.user_algo_type_count[row_dict['username']]:
                self.user_algo_type_count[row_dict['username']][row_dict['algo_type']] = {}

            # Check if the algo_name exists for this algorithm type, if not, initialize it
            if row_dict['algo_name'] not in self.user_algo_type_count[row_dict['username']][row_dict['algo_type']]:
                
                if row_dict['algo_type'] == 'diaoyu':

                    buy_amt = int(row_dict['qty']) if int(row_dict['spread']) > 0 else 0
                    sell_amt = int(row_dict['qty']) if int(row_dict['spread']) < 0 else 0
                else:
                    buy_amt = int(row_dict['qty']) if int(row_dict['spread']) < 0 else 0
                    sell_amt = int(row_dict['qty']) if int(row_dict['spread']) > 0 else 0

                self.user_algo_type_count[row_dict['username']][row_dict['algo_type']][row_dict['algo_name']] = {
                    'buy': buy_amt,
                    'sell': sell_amt,
                    'filled_amount': 0,
                    'remaining_amount': buy_amt if buy_amt >0 else sell_amt,
                    'average_fill_price': 0.0,
                    'total_executed_value': 0.0,
                    'max_position_limit': 100,
                    'start_time': None,
                    'end_time': None,
                    'execution_log': [],
                    'error_log': [],
                    'status': False
                }

          
        logger.info(f"COUNT AFTER EVERYTHING {self.user_algo_type_count}")


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
            # row_dict['trade_direction'] = row[11]
            row_dict['htx_apikey'] = row[11]
            row_dict['htx_secretkey'] = row[12]
            row_dict['okx_apikey'] = row[13]
            row_dict['okx_secretkey'] = row[14]
            row_dict['okx_passphrase'] = row[15]
            row_dict['filled_vol'] = 0



            # Create a unique instance ID
            instance_id = f"{row_dict['username']}_{row_dict['algo_type']}_{row_dict['algo_name']}"

            row_dict['user_algo_type_count'] = self.user_algo_type_count
            self.shared_states[instance_id] = self.manager.dict(row_dict)
            # each multiprocess should have its own connection to db
            logger.debug(f"CREATING NEW STRAT with - {self.shared_states[instance_id]}")
            self.initialise_strat(row_dict['algo_type'],instance_id,psycopg2.connect(**DB_CONFIG).cursor())

  

        for p in self.processes:
            p.join()
        


        
    def handle_termination_signal(self,signum, frame):
        """Signal handler for termination signals (SIGINT, SIGTERM)."""
        print(f"Received signal {signum}, cleaning up and exiting...")
        # Gracefully terminate child processes
        for process in self.processes:
            process.terminate()  # Gracefully terminate the worker processes
            process.join()       # Wait for processes to finish

        print("All processes terminated. Exiting...")
        sys.exit(0)  # Exit the main process after cleanup

    def stop_all(self):
        """Stop all strategies and terminate their processes."""
        print("Stopping all strategies and processes...")
        for instance_id, (strat, process) in self.algos.items():
            strat.stop_clients()


class DBListener(threading.Thread):
    """Simulates a database listener."""
    def __init__(self, factory):
        super().__init__()
        self.running = True
        self.factory = factory
        self.conn = psycopg2.connect(**DB_CONFIG)
        
    def run(self):
    
        self.conn = psycopg2.connect(**DB_CONFIG)
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
                # logger.debug(f"ALGO DETAILS:{algo_details}")
                # logger.debug(algo_details)
                operation = algo_details['operation'] # db operations: update,insert...
                # json_data = algo_details['data']

                # # Initialize and start new AlgoRunTime instance
              
                if operation == "DELETE":
                    json_data = algo_details['old_data']
                    # Initialize and start new AlgoRunTime instance
                    username = json_data['username']
                    algo_type = json_data['algo_type']
                    algo_name = json_data['algo_name']
                    instance_id = f"{username}_{algo_type}_{algo_name}"
                    self.factory.remove_algo(instance_id,json_data)

                else:
                    logger.info("UPDATE")
                    json_data = algo_details['data']
                    # Initialize and start new AlgoRunTime instance
                    username = json_data['username']
                    algo_type = json_data['algo_type']
                    algo_name = json_data['algo_name']
                    instance_id = f"{username}_{algo_type}_{algo_name}"
                    # logger.debug("ALGO UPDATED!!!!!!!!!!!!!!")
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
                        self.factory.add_algo(instance_id,new_algo_detail)
                    # For updates
                    else:
                        self.factory.update_algo(instance_id,algo_details)

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
        # print("Executing all algorithms...")
        factory.execute_all()
            # time.sleep(5)
    except KeyboardInterrupt:
        logger.error("KeyboardInterrupt detected. Shutting down gracefully...")
        # print("KeyboardInterrupt detected. Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Error detected: {e}")
        # print(f"An unexpected error occurred: {e}")
    finally:
        # Ensure cleanup happens no matter what
        # print("Cleaning up...")
        factory.stop_all()
        db_listener.stop()
        factory.handle_termination_signal(None,None)
        db_listener.join()

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5099)
