import datetime
import json
import uuid
import threading
import asyncio
import psycopg2
import sys
import redis
sys.path.append('/var/www/html/orderbook/htx2')
sys.path.append('/var/www/html/orderbook/htx2/alpha')
import traceback
import gc
# from app.trading_engines.htxTradeFuturesApp import place_limit_contract_order
from app.htx2.HtxOrderClass import HuobiCoinFutureRestTradeAPI
from okx import Trade
# from okx.websocket.WsPublicAsync import WsPublicAsync
# from websockets.exceptions import ConnectionClosedError

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
logger = logging.getLogger('Diaoxia')
logger.setLevel(logging.DEBUG)  # Set log level
# Add the file handler to the logger
logger.addHandler(file_handler)
from datetime import datetime




# CONFIG
import configparser
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
config.read(config_file_path)
config_source = 'redis'
REDIS_HOST = config[config_source]['host']
REDIS_PORT = config[config_source]['port']
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# config_source = 'localdb'
config_source = config['dbchoice']['db']
dbusername = config[config_source]['username']
dbpassword = config[config_source]['password']
dbname = config[config_source]['dbname']
import time
from app.strategies.connection_helper import OkxBbo,HtxBbo ,HtxPositions


# Database configuration
DB_CONFIG = {
    "dbname": dbname,
    "user": dbusername,
    "password": dbpassword,
    "host": "localhost",
    "port": 5432
}

# for Diaoxia, positive spread means buying on lead and selling on lag while negative spread means selling on lead and buying on lag. 
# Diaoxia conditions
# - spread matches
# - qty matches
#   - if qty doesnt match in 1 trade, it will be carry on until the total filled matches the qty
# - lead and lag exchanges specified

class Diaoxia:
    best_bid: float 
    best_bid_sz:int
    best_ask: float
    best_ask_sz:int
    htx_best_bid: float
    htx_best_bid_sz: int
    htx_best_ask:float
    htx_best_ask_sz:int
    
    def __init__(self,row_dict,cursor):
        # shared_state
        self.row = row_dict
        # self.row = row_dict
        self.username = self.row['username']
        self.algotype = self.row['algo_type']
        self.algoname = self.row['algo_name']
        self.htx_apikey =    self.row['htx_apikey']
        self.htx_secretkey = self.row['htx_secretkey']
        self.htx_tradeapi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",self.row['htx_apikey'],self.row['htx_secretkey'])
        self.okx_api_key = self.row['okx_apikey']
        self.okx_secret_key = self.row['okx_secretkey']
        self.okx_passphrase = self.row['okx_passphrase']

        self.okx_tradeapi = Trade.TradeAPI(self.okx_api_key, self.okx_secret_key,self.okx_passphrase, False, '0')
        # db
        self.dbsubscriber = None
        self.db_thread = None
        # okx
        self.loop = None
        self.row['okx_client'] = None
        self.row['htx_client'] = None
        self.htx_thread = None
        # from okxbbo
        self.best_bid = None
        self.best_bid_sz = None
        self.best_ask = None
        self.best_ask_sz = None
        # from htx
        self.htx_best_bid = None
        self.htx_best_bid_sz = None
        self.htx_best_ask = None
        self.htx_best_ask_sz = None
        # from user input
        self.qty = self.row['qty']
        self.ccy = self.row['ccy']
        self.spread = self.row['spread']
        self.lead_exchange = self.row['lead_exchange']
        self.lag_exchange =  self.row['lag_exchange']
        # true or false state
        self.state = self.row['state']
        self.instrument = self.row['instrument']
        self.contract_type = self.row['contract_type']

        # derived from okx and user input
        self.limit_buy_price = None
        self.limit_buy_size = None
        self.row['order_id'] = None
        self.lead_direction = None
        self.okx_direction = None
        self.received_data = None  # Variable to store received data

        # status
        self.row['filled_vol'] = 0
        self.lead_is_filled = False

        # db connection
        self.cursor = cursor
        # throttle
        self.last_call_time = 0
        self.call_interval = 0.1

        # lock for race conditions
        self.order_lock = threading.Lock() 
        self.excecution_lock = asyncio.Lock()

        # positions details
        self.htx_availability = None
        self.htx_order_type = None
        self.htx_pos_thread = None

        self.diaoxia_availability = None
        self.diaoxia_offset = None

        self.connect_db()

        self.last_update_okx = time.time()
        self.last_update_htx = time.time()

        self.check_count = 0
        self.check_requirement_count = 1 # means 2 because it checks on 0 and checks on 1 and fire 

        self.total_buy = 0
        self.total_sell = 0
        self.diaoyu_buy = 0
        self.diaoyu_sell = 0
        self.diaoxia_buy = 0
        self.diaoxia_sell = 0
        self.is_order_running = False

        self.filled_amount = None
        self.remaining_amount = None


    # connection with okx bbo
    async def run_okx_bbo(self):
        """Run the OkxBbo WebSocket client."""
        self.row['okx_client'] = OkxBbo()
        currency_pairs = ["BTC-USD-SWAP"]  # Add more pairs as needed
        channel = "bbo-tbt"
        await self.row['okx_client'].run(channel, currency_pairs, self.okx_publicCallback)


    async def run_htx_positions(self):
        """Run the HtxPositions WebSocket client."""
    
        access_key = self.htx_apikey
        secret_key = self.htx_secretkey
        # for swaps
        notification_url = 'wss://api.hbdm.com'
        notification_endpoint = '/swap-notification'
        
        notification_subs = [
            {
                "op": "sub",
                "cid": str(uuid.uuid1()),
                "topic": "positions.BTC-USD"
            }
        ]
        # swap client
        htx_pos_client = HtxPositions(notification_url, notification_endpoint, access_key, secret_key,self.username,self.algoname)
        self.htx_pos_client = htx_pos_client
        await self.htx_pos_client.start(notification_subs, auth=True, callback=self.htx_position_publicCallback)


    async def run_htx_bbo(self):
        """Run the HtxPositions WebSocket client asynchronously."""
        access_key = self.htx_apikey
        secret_key = self.htx_secretkey
        notification_url = 'wss://api.hbdm.com'
        notification_endpoint = '/swap-ws'

        notification_subs = [
            {
                "id": str(uuid.uuid1()),
                "sub": "market.BTC-USD.bbo"
            }
        ]

        # Initialize the WebSocket client
        ws_client = HtxBbo(notification_url, notification_endpoint, access_key, secret_key,self.username,self.algoname)
        self.htx_client = ws_client

        # Start WebSocket client asynchronously
        await self.htx_client.start(notification_subs, auth=True, callback=self.htx_publicCallback)

    async def start_clients_sync(self):
        """Start all WebSocket clients concurrently using asyncio."""
        tasks = []

        if self.lead_exchange == 'htx' or self.lag_exchange == 'htx':
            tasks.append(self.run_htx_positions())  # Ensure these are async functions
            tasks.append(self.run_htx_bbo())

        if self.lead_exchange == 'okx' or self.lag_exchange == 'okx':
            tasks.append(self.run_okx_bbo())

        # Run all tasks asynchronously
        await asyncio.gather(*tasks)

    def start_clients(self):
        """Sync wrapper to run start_clients() inside multiprocessing."""
        asyncio.run(self.start_clients_sync())  # En
        
    def stop_clients(self):
        """Stop both WebSocket clients gracefully."""
        if self.row['okx_client']:
            self.row['okx_client'].close()
            self.row['okx_client'].unsubscribe()
            logger.debug(f"{self.username}|{self.algoname}|CLOSE AND UNSUBSCRIBED FROM OKX")
        self.update_db()

    # def determine_trade_type(self,algo_json_dict):
        
    #     net_availability = int(algo_json_dict['net_availability'])

    #     total_buy = 0
    #     total_sell = 0
    #     diaoyu_buy = 0
    #     diaoyu_sell = 0
    #     diaoxia_buy = 0
    #     diaoxia_sell = 0

 
    #     for algo_type, algos in algo_json_dict.items():
    #         if algo_type == 'net_availability':
    #             continue

    #         for algo_name, stats in algos.items():
    #             if stats['status']:
    #                 buy = stats.get('buy', 0)
    #                 sell = stats.get('sell', 0)
    #                 filled = stats.get('filled_amount', 0)

    #                 # Determine the net direction
    #                 if buy > 0 and sell == 0:
    #                     buy -= filled
    #                 elif sell > 0 and buy == 0:
    #                     sell -= filled
    #                 # If it's a mix (e.g., buy and sell both > 0), we assume filled is equally from both? Customize this if needed.

    #                 total_buy += buy
    #                 total_sell += sell

    #                 if algo_type == 'diaoyu':
    #                     diaoyu_buy += buy
    #                     diaoyu_sell += sell
    #                 elif algo_type == 'diaoxia':
    #                     diaoxia_buy += buy
    #                     diaoxia_sell += sell


    #     print("Total Buy:", total_buy)
    #     print("Total Sell:", total_sell)
    #     print("Diaoyu Buy:", diaoyu_buy)
    #     print("Diaoyu Sell:", diaoyu_sell)
    #     print("Diaoxia Buy:", diaoxia_buy)
    #     print("Diaoxia Sell:", diaoxia_sell)

    #     self.total_buy = total_buy
    #     self.total_sell = total_sell
    #     self.diaoyu_buy = diaoyu_buy
    #     self.diaoyu_sell = diaoyu_sell
    #     self.diaoxia_buy = diaoxia_buy
    #     self.diaoxia_sell = diaoxia_sell

  
    #     # Base availability logic
    #     remaining_pos = net_availability + diaoyu_buy - diaoyu_sell  # Adjust for diaoyu activity
        
    #     # Determine diaoxia trade permissions
    #     self.trade_type = {"buy": None, "sell": "open"}  # Default diaoxia can always sell (continue shorting)



    #     if net_availability < 0 and diaoxia_buy > 0:
    #         # Short position: Allow buy only to close
    #         if abs(remaining_pos) >= diaoxia_buy:
    #             self.trade_type["buy"] = "close"

    #     elif net_availability > 0 and diaoxia_sell > 0:
    #         # Long position: Allow sell only to close
    #         if remaining_pos >= diaoxia_sell:
    #             self.trade_type["sell"] = "close"

    #     elif net_availability == 0:
    #         # No position: Both directions allowed
    #         self.trade_type["buy"] = "open"
    #         self.trade_type["sell"] = "open"

    #     return self.trade_type


    def determine_trade_type(self,algo_json_dict,net_availability,fileld_amount,remaining_amount):
        self.trade_type = {"buy": None, "sell": "open"}  # Default diaoxia can always sell (continue shorting)
        net_availability = int(net_availability)


        total_buy = 0
        total_sell = 0
        diaoyu_buy = 0
        diaoyu_sell = 0
        diaoxia_buy = 0
        diaoxia_sell = 0
 
        for algo_type, algos in algo_json_dict.items():
            if algo_type == 'net_availability':
                continue

            for algo_name, stats in algos.items():
                if stats['status']:
                    buy = stats.get('buy', 0)
                    sell = stats.get('sell', 0)
                    filled = stats.get('filled_amount', 0)

                    # Determine the net direction
                    if buy > 0 and sell == 0:
                        buy -= filled
                    elif sell > 0 and buy == 0:
                        sell -= filled
                    # If it's a mix (e.g., buy and sell both > 0), we assume filled is equally from both? Customize this if needed.

                    total_buy += buy
                    total_sell += sell

                    if algo_type == 'diaoyu':
                        diaoyu_buy += buy
                        diaoyu_sell += sell
                    elif algo_type == 'diaoxia':
                        diaoxia_buy += buy
                        diaoxia_sell += sell


        print("Total Buy:", total_buy)
        print("Total Sell:", total_sell)
        print("Diaoyu Buy:", diaoyu_buy)
        print("Diaoyu Sell:", diaoyu_sell)
        print("Diaoxia Buy:", diaoxia_buy)
        print("Diaoxia Sell:", diaoxia_sell)

        self.total_buy = total_buy
        self.total_sell = total_sell
        self.diaoyu_buy = diaoyu_buy
        self.diaoyu_sell = diaoyu_sell
        self.diaoxia_buy = diaoxia_buy
        self.diaoxia_sell = diaoxia_sell



        # logger.debug(f"{net_availability}|{fileld_amount},{remaining_amount}")
        # net_availability = int(algo_json_dict['net_availability'])
        if net_availability < 0 :
            if remaining_amount <= abs(net_availability):
                self.trade_type["buy"] = "close"
        elif net_availability>0:
            if remaining_amount >= abs(net_availability):
                self.trade_type['sell'] = "close"

        elif net_availability == 0:
            # No position: Both directions allowed
            self.trade_type["buy"] = "open"
            self.trade_type["sell"] = "open"

        return self.trade_type

    def run_tasks(self, tasks):
        async def runner():
            await asyncio.gather(*tasks)

        try:
            # If we're already in an async context, schedule it
            loop = asyncio.get_running_loop()
            return asyncio.create_task(runner())
        except RuntimeError:
            # Not in an async context — safe to use asyncio.run
            return asyncio.run(runner())

    async def run_orders_and_update_state(self, min_avail_amt_buy,trade_type):
        await asyncio.gather(
            self.place_market_order_htx(min_avail_amt_buy, self.lag_direction,trade_type),
            self.place_market_order_okx(min_avail_amt_buy, self.lead_direction,trade_type),
        )

        # # Step 1: Read the entire shared user_algo_type_count object
        # user_data = self.row['user_algo_type_count']

        # # Step 2: Modify the nested algo data
        # algo_data = user_data[self.username][self.algotype][self.algoname]
        # algo_data['filled_amount'] += min_avail_amt_buy
        # algo_data['remaining_amount'] -= min_avail_amt_buy

        # # Step 3: Write it back to ensure the shared state gets updated
        # user_data[self.username][self.algotype][self.algoname] = algo_data
        # self.row['user_algo_type_count'] = user_data

        # # Re-assign the modified dict back to ensure update is synced across processes
        # user_algo_type_count_dict[self.algotype][self.algoname] = algo_data

        self.filled_amount += min_avail_amt_buy
        self.remaining_amount -= min_avail_amt_buy



        



    def check_condition(self, spread :int,filled_amt,remaining_amount,trade_type, callback):
        try:
            check_condition_time_start = time.time()
            # print(current_time,max(self.last_update_okx, self.last_update_htx) , current_time - max(self.last_update_okx, self.last_update_htx) )
            if check_condition_time_start - min(self.last_update_okx, self.last_update_htx) > 0.050:
                # logger.debug("Warning: Order book data is stale!")
                self.is_order_running = False
                return
            logger.debug(f"{self.username}|{self.algoname}|fa:{self.filled_amount}|ra:{self.remaining_amount}")
            # logger.debug("HELLO CHECKING CONDITION")
            
            check_diaoxia_offset_time_start = time.time()
           
            check_diaoxia_offset_time_end = time.time() - check_diaoxia_offset_time_start
            print(check_diaoxia_offset_time_end)
            try:
                if self.remaining_amount == 0:
                    self.filled_amount = None
                    self.remaining_amount = None
                    self.update_db()
                    # self.row['filled_vol'] = 0 # reset when algo is completed and switched off 
                    return
            
                # Log order book data
                logger.debug(f"{self.username}|{self.algoname}|OKX↑:{datetime.fromtimestamp(self.last_update_okx).strftime('%H:%M:%S.%f')[:-3]}|HTX↑:{datetime.fromtimestamp(self.last_update_htx).strftime('%H:%M:%S.%f')[:-3]}|htx:{self.htx_best_bid}|{self.htx_best_bid_sz}|{self.htx_best_ask}|{self.htx_best_ask_sz}|okx:{self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz}|Net_Avail:{self.net_volume} TL_B:{self.total_buy}|TL_S:{self.total_sell}|DY_B:{self.diaoyu_buy}|DY_S:{self.diaoyu_sell}|DX_B:{self.diaoxia_buy}|DX_S:{self.diaoxia_sell}")
            
                # Precompute spread conditions
                bid_ask_spread_1 = float(self.htx_best_bid) - float(self.best_ask)
                bid_ask_spread_2 = float(self.best_bid) - float(self.htx_best_ask)


                # hardcode test
                current_time = time.localtime(time.time())
                # Check if it's 15:35
                if current_time.tm_hour == 15 and current_time.tm_min == 38:
                    print("It is 15:35 right now!")
                    # testing to sell htx which is the left side of the ui
                    bid_ask_spread_1 = 52
                else:
                    print(f"It is currently {current_time.tm_hour}:{current_time.tm_min:02d}")

                # Determine min available amount for orders
                min_avail_amt_buy = min(int(self.htx_best_bid_sz), int(self.best_ask_sz), 100, remaining_amount,1)
                min_avail_amt_sell = min(int(self.best_bid_sz), int(self.htx_best_ask_sz), 100, remaining_amount,1)
                okx_update = datetime.fromtimestamp(self.last_update_okx).strftime('%H:%M:%S.%f')[:-3]
                htx_update = datetime.fromtimestamp(self.last_update_htx).strftime('%H:%M:%S.%f')[:-3]

                # sell htx
                # Check spread conditions for order execution
                self.order_tasks = []
                if spread > 0 and bid_ask_spread_1 >= spread:
                    logger.debug(f"{self.username}|{self.algoname}|OKX↑:{datetime.fromtimestamp(self.last_update_okx).strftime('%H:%M:%S.%f')[:-3]}|HTX↑:{datetime.fromtimestamp(self.last_update_htx).strftime('%H:%M:%S.%f')[:-3]}|htx:{self.htx_best_bid}|{self.htx_best_bid_sz}|{self.htx_best_ask}|{self.htx_best_ask_sz}|okx:{self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz}|Net_Avail:{self.net_volume} TL_B:{self.total_buy}|TL_S:{self.total_sell}|DY_B:{self.diaoyu_buy}|DY_S:{self.diaoyu_sell}|DX_B:{self.diaoxia_buy}|DX_S:{self.diaoxia_sell} SPREAD DETECTED Count:{self.check_count} ")
                    
                    # asyncio.create_task(self.run_orders_and_update_state(min_avail_amt_buy,trade_type))
                    return True
                    
                # buy htx
                elif spread < 0 and bid_ask_spread_2 >= abs(spread):
                    
                    logger.debug(f"{self.username}|{self.algoname}|OKX↑:{datetime.fromtimestamp(self.last_update_okx).strftime('%H:%M:%S.%f')[:-3]}|HTX↑:{datetime.fromtimestamp(self.last_update_htx).strftime('%H:%M:%S.%f')[:-3]}|htx:{self.htx_best_bid}|{self.htx_best_bid_sz}|{self.htx_best_ask}|{self.htx_best_ask_sz}|okx:{self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz}|Net_Avail:{self.net_volume} TL_B:{self.total_buy}|TL_S:{self.total_sell}|DY_B:{self.diaoyu_buy}|DY_S:{self.diaoyu_sell}|DX_B:{self.diaoxia_buy}|DX_S:{self.diaoxia_sell} SPREAD DETECTED Count:{self.check_count} ")
                
                    # asyncio.create_task(self.run_orders_and_update_state(min_avail_amt_buy,trade_type))
                    return True

                self.check_count = 0
                
                
    
                check_condition_time_end = time.time() - check_condition_time_start
                print(f"DIAOXIA OFFSET_TIME:{check_diaoxia_offset_time_end}| CONDITION CHECK:{check_condition_time_end} TL_TIME:{check_diaoxia_offset_time_end+check_condition_time_end}")

            except Exception as e:
                self.update_db()
                logger.debug(f"Error occurred in check_condition: {traceback.format_exc}")
                raise e
        except Exception as e:
            logger.error(e)
        


    def okx_publicCallback(self,message):
        with self.order_lock:
            try:
                # print(f"OKX POSITTION:{message}")

                """Callback function to handle incoming messages."""
                json_data = json.loads(message)
                if json_data.get('data'):
                    currency_pair = json_data["arg"]["instId"]
                    # print(json_data)
                    self.best_bid = json_data["data"][0]["bids"][0][0]
                    self.best_bid_sz = json_data["data"][0]["bids"][0][1]
                    self.best_ask = json_data["data"][0]["asks"][0][0]
                    self.best_ask_sz = json_data["data"][0]["asks"][0][1]
                    # Place limit order on lagging party e.g htx - htx requires cancel and place new order for amend
                    # Order will be placed to buy on htx side
                    # spread = float(self.spread)
                    self.limit_buy_price = float(self.best_bid) - float(self.spread)
                    self.limit_buy_size = self.qty
                    self.lead_direction, self.lag_direction = ('buy', 'sell') if float(self.spread) > 0 else ('sell', 'buy')
                    self.last_update_okx = time.time()
                    self.state = self.row['user_algo_type_count'][self.username][self.algotype][self.algoname]['status']

                    user_algo_type_count_dict = self.row['user_algo_type_count'][self.username]
                    # filled_amt = user_algo_type_count_dict[self.algotype][self.algoname]['filled_amount']
                    # remaining_amount = user_algo_type_count_dict[self.algotype][self.algoname]['remaining_amount']
                    buy_amt = user_algo_type_count_dict[self.algotype][self.algoname]['buy']
                    sell_amt = user_algo_type_count_dict[self.algotype][self.algoname]['sell']

                    # initialising with dictionary amt
                    if self.remaining_amount == None:
                        logger.debug("filled amt is none")
                        self.filled_amount =  user_algo_type_count_dict[self.algotype][self.algoname]['filled_amount']
                        self.remaining_amount = user_algo_type_count_dict[self.algotype][self.algoname]['remaining_amount']


                    # logger.debug(f"net_avail:{user_algo_type_count_dict['net_availability']}| remaining_amount:{remaining_amount}| filled_amt:{filled_amt} |total_sell:{self.total_sell}|total_buy:{self.total_buy}")
                    trade_type = self.determine_trade_type(user_algo_type_count_dict,user_algo_type_count_dict['net_availability'],self.filled_amount,self.remaining_amount)
                    

                    if self.state:

                        if ((user_algo_type_count_dict['net_availability'] < 0 and self.total_buy> abs(user_algo_type_count_dict['net_availability']) and self.filled_amount ==0) or (user_algo_type_count_dict['net_availability'] > 0 and self.total_sell > abs(user_algo_type_count_dict['net_availability']) and self.filled_amount ==0)):
                            logger.debug("NET AVAIL LESSER THAN required")
                            self.update_db()
                        

                        if self.is_order_running:
                            return

                        if self.check_condition(float(self.spread),self.filled_amount,self.remaining_amount,trade_type,'okx_callback'):
                            if self.check_count == self.check_requirement_count:
                                self.is_order_running = True
                                logger.debug(trade_type)
                                # asyncio.create_task(self.check_condition(float(self.spread),self.filled_amount,self.remaining_amount,trade_type,'okx_callback'))
                                        # Determine min available amount for orders
                                min_avail_amt_buy = min(int(self.htx_best_bid_sz), int(self.best_ask_sz), 100, self.remaining_amount,1)
                                min_avail_amt_sell = min(int(self.best_bid_sz), int(self.htx_best_ask_sz), 100, self.remaining_amount,1)
                                asyncio.create_task(self.run_orders_and_update_state(min_avail_amt_buy,trade_type))

                                self.check_count = 0
                                self.is_order_running = False
                                
                            else:
                                self.check_count += 1
                                time.sleep(self.call_interval)
                    
                
            except Exception as e:
                logger.error(f"{self.username}|{self.algoname}|OKX PUBLICCALLBACK ERROR:{e}")

    async def place_order_htx_helper(self,tradeApi, instId, volume, direction, offset):
        
        return await tradeApi.place_order(
            instId,
            body={
                "contract_code": instId,
                "created_at": datetime.now().isoformat(),
                "volume": str(volume),
                "direction": direction,
                "offset": offset,
                "lever_rate": 5,
                "order_price_type": "optimal_20"
            }
        )
    

    def htx_position_publicCallback(self,message):
        with self.order_lock:
            # print(f"HTX POSITTION:{message}")
            try:
                if message.get('op') == "notify":
                    # logger.debug(message)
                    if message.get('data'):
                        # logger.debug(message.get('data'))
                        # total net_volume is total position. i.e net_availability == 0 means theres no position and for htx, direction will be open
                        self.net_volume = sum(pos['volume'] if pos['direction'] == 'buy' else -pos['volume'] for pos in message['data'])

                        # THIS IS A UNIQUE WAY OF DOING THINGS BECAUSE ITS IN THE SHARED STATE
                        user_data = self.row['user_algo_type_count']
                        user_data[self.username]['net_availability'] = self.net_volume

                        # logger.debug(user_data[self.username]['net_availability'])
                        self.row['user_algo_type_count'] = user_data  
                     
            except Exception as e:
                logger.error(f"Error{traceback.format_exc()}")

    async def place_market_order_htx(self,size,direction,trade_type):
        # Use limit_buy_price and limit_buy_size directly instead of `self.limit_buy_price`
            try:
                result = await self.place_order_htx_helper(self.htx_tradeapi, self.ccy.replace('-SWAP',''), size, direction,trade_type[direction])
                logger.debug(f"{self.username}|{self.algoname}|OKX↑:{datetime.fromtimestamp(self.last_update_okx).strftime('%H:%M:%S.%f')[:-3]}|HTX↑:{datetime.fromtimestamp(self.last_update_htx).strftime('%H:%M:%S.%f')[:-3]}|htx:{self.htx_best_bid}|{self.htx_best_bid_sz}|{self.htx_best_ask}|{self.htx_best_ask_sz}|okx:{self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz}|Net_Avail:{self.net_volume} TL_B:{self.total_buy}|TL_S:{self.total_sell}|DY_B:{self.diaoyu_buy}|DY_S:{self.diaoyu_sell}|DX_B:{self.diaoxia_buy}|DX_S:{self.diaoxia_sell} htx_place_market_order result:{result}")

                user_algo_type_count_dict = self.row['user_algo_type_count'][self.username]
                filled_amt = user_algo_type_count_dict[self.algotype][self.algoname]['filled_amount']
                remaining_amount = user_algo_type_count_dict[self.algotype][self.algoname]['remaining_amount']

                logger.debug(f"net_avail:{user_algo_type_count_dict['net_availability']}| remaining_amount:{remaining_amount}| filled_amt:{filled_amt} |total_sell:{self.total_sell}|total_buy:{self.total_buy}")
                # logger.debug(f"{self.username}|{self.algoname}|OKX↑:{datetime.fromtimestamp(self.last_update_okx).strftime('%H:%M:%S.%f')[:-3]}|HTX↑:{datetime.fromtimestamp(self.last_update_htx).strftime('%H:%M:%S.%f')[:-3]} htx: {self.htx_best_bid}|{self.htx_best_bid_sz}|{self.htx_best_ask}|{self.htx_best_ask_sz}  okx: {self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz} {self.row['user_algo_type_count'][self.username]}|{self.diaoxia_availability}|{self.diaoxia_offset[direction]}  htx_place_market_order result:{result}")

            except Exception as e:
                self.update_db()
                logger.error(f"Error{traceback.format_exc()}")

                
    def htx_publicCallback(self,message):
        with self.order_lock:
            # print(f"HTX ORDERBOOK:{message}")
            try:
                if message.get('tick'):
                    self.last_update_htx = time.time()

                    self.htx_best_bid = message['tick']['bid'][0]
                    self.htx_best_bid_sz = message['tick']['bid'][1]
                    self.htx_best_ask = message['tick']['ask'][0]
                    self.htx_best_ask_sz = message['tick']['ask'][1]
                    # if self.row['user_algo_type_count'][self.username][self.algotype][self.algoname]['status']:
                    self.state = self.row['user_algo_type_count'][self.username][self.algotype][self.algoname]['status']
                    # if self.row['user_algo_type_count'][self.username][self.algotype][self.algoname]['status']:
                    # if self.state and self.row['user_algo_type_count'][self.username][self.algotype][self.algoname]['remaining_amount'] != 0 :
                    #     self.check_condition(float(self.spread),'htx_callback')
                  
                    # logger.debug(f"{self.username}|{self.algoname}|HTX BBO:{message}")
                    
                    
            except Exception as e:
                logger.error(f"{self.username}|{self.algoname}| HTX PUBLICCALLBACK:", e)

    async def place_market_order_okx(self,size,direction,trade_type):
        try:
            # Initialize TradeAPI
            tradeApi = self.okx_tradeapi
            result = tradeApi.place_order(
                instId= 'BTC-USD-SWAP',
                tdMode= "cross", 
                side= direction, 
                posSide= '', 
                ordType= 'market',
                sz= size
            )
            result['data'][0]['exchange']='okx'
            
            # OKX MARKET ORDER IS SUCCESSFUL
            if result["code"] == "0":
                result['data'][0]['sCode'] = 200
                self.row['order_id']  = None
            else:
                result['data'][0]['sCode'] = 400
                logger.error('OKX MARKET TRADE FAILED')

            logger.debug(f"{self.username}|{self.algoname}|OKX↑:{datetime.fromtimestamp(self.last_update_okx).strftime('%H:%M:%S.%f')[:-3]}|HTX↑:{datetime.fromtimestamp(self.last_update_htx).strftime('%H:%M:%S.%f')[:-3]}|htx:{self.htx_best_bid}|{self.htx_best_bid_sz}|{self.htx_best_ask}|{self.htx_best_ask_sz}|okx:{self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz}|Net_Avail:{self.net_volume} TL_B:{self.total_buy}|TL_S:{self.total_sell}|DY_B:{self.diaoyu_buy}|DY_S:{self.diaoyu_sell}|DX_B:{self.diaoxia_buy}|DX_S:{self.diaoxia_sell}|okx_place_order result:{result} ")
            # logger.debug(f"{self.username}|{self.algoname}|OKX↑:{datetime.fromtimestamp(self.last_update_okx).strftime('%H:%M:%S.%f')[:-3]}|HTX↑:{datetime.fromtimestamp(self.last_update_htx).strftime('%H:%M:%S.%f')[:-3]} htx: {self.htx_best_bid}|{self.htx_best_bid_sz}|{self.htx_best_ask}|{self.htx_best_ask_sz}  okx: {self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz} {self.row['user_algo_type_count'][self.username]}|{self.diaoxia_availability}|{self.diaoxia_offset} |okx_place_order result:{result} ")

            return result

        except Exception as e:
            logger.error(f"{self.username}|{self.algoname}|okx_place_market_order ERROR:{e}")

    def connect_db(self):
        """Ensures the database connection is open and initializes the cursor."""
        if self.cursor.connection.closed:
            self.cursor = psycopg2.connect(**DB_CONFIG).cursor()  # Reconnect if closed
   

    def update_db(self):
        # Input should be unique so it should be username,algo_type and algoname
        # Update based on parameters. by updating here it will trigger the algo listener
        try:
       
            self.connect_db()
            query = "update algo_dets set state = false where username = %s and algo_type=%s and  algo_name=%s"
            # self.cursor.connection.commit()
            with self.cursor.connection.cursor() as cursor:
                cursor.execute(query, (self.username, self.algotype, self.algoname))
                self.cursor.connection.commit()
            self.cursor.connection.close()
            # https://stackoverflow.com/questions/64995178/decryption-failed-or-bad-record-mac-in-multiprocessing
            logger.debug(f"{self.username}|{self.algoname}|Database Updated")
     

        
        except Exception as e:
            logger.error(f"{self.username}|{self.algoname}|DATABASE Error:{traceback.format_exc()}")
        # finally:
        #     self.cursor.close()  # Close the cursor
        #     return 



# if __name__ == '__main__':
    # 1 strat = 1 algo 
    # try:
        # params = {'username': 'brennan', 'algo_type': 'diaoxia', 'algo_name': 'test9', 'lead_exchange': 'okx', 'lag_exchange': 'htx', 'spread': '10', 'qty': '1', 'ccy': 'BTC-USD-SWAP', 'instrument': 'swap', 'contract_type': 'thisweek', 'state': False, 'htx_apikey': 'nbtycf4rw2-5475d1b1-fd22adf0-83746', 'htx_secretkey': 'c5a5a686-b39d1d16-79864b22-f3e72', 'okx_apikey': 'a0de3940-5679-4939-957a-51c87a8502d9', 'okx_secretkey': 'FA44BCAAC3788C2AB4AFC77047930792', 'okx_passphrase': 'falconstead@Trading2024'}
        # strat = Diaoxia(params,psycopg2.connect(**DB_CONFIG).cursor())
        # strat.start_clients()
    # except KeyboardInterrupt:
    #     print("Stopping clients...")
        # strat.stop_clients()
