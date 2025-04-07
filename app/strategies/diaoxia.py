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

    def determine_trade_type(self,pos, algotypes):
        """
        Determines available trade actions based on position and strategy activity.
        :param pos: Current position (positive = long, negative = short)
        :param algotypes: Dictionary of trade strategies {'strategy_name': {'buy': x, 'sell': y}}
        :return: Dict of trade types allowed for diaoxia {'buy': 'open/close/None', 'sell': 'open'}
        """

        diaoyu = algotypes.get("diaoyu", {"buy": 0, "sell": 0})
        diaoxia = algotypes.get("diaoxia", {"buy": 0, "sell": 0})

        # Base availability logic
        remaining_pos = pos + diaoyu["buy"] - diaoyu["sell"]  # Adjust for diaoyu activity
        
        # Determine diaoxia trade permissions
        trade_type = {"buy": None, "sell": "open"}  # Default diaoxia can always sell (continue shorting)

        if pos < 0:  # Short position
            if diaoxia["buy"] > 0:
                trade_type["buy"] = "close" if abs(remaining_pos) >= diaoxia["buy"] else None  # Can only cover short
        elif pos > 0:  # Long position
            if diaoxia["sell"] > 0:
                trade_type["sell"] = "close" if remaining_pos >= diaoxia["sell"] else None  # Can only close long
        else:  # No position
            trade_type["buy"] = "open"
            trade_type["sell"] = "open"

        return trade_type



    def check_condition(self, spread :int, callback):
        current_time = time.time()
        # print(current_time,max(self.last_update_okx, self.last_update_htx) , current_time - max(self.last_update_okx, self.last_update_htx) )
        if current_time - min(self.last_update_okx, self.last_update_htx) > 0.050:
            # logger.debug("Warning: Order book data is stale!")
            return

        self.total_sell = -(self.row['user_algo_type_count'][self.username]['diaoyu']['sell'] + self.row['user_algo_type_count'][self.username]['diaoxia']['sell'])
        self.total_buy = self.row['user_algo_type_count'][self.username]['diaoyu']['buy'] + self.row['user_algo_type_count'][self.username]['diaoxia']['buy']
        # logger.debug(f"net_vol:{self.net_volume}|total_sell:{self.total_sell},total_buy:{self.total_buy},algo_count: {self.row['user_algo_type_count'][self.username]}")

        
        try:
            if self.row['filled_vol'] == int(self.qty):
                self.update_db()
                self.row['filled_vol'] = 0 # reset when algo is completed and switched off 
                return

            if not self.row['state']:
                self.row['filled_vol'] = 0  # Reset when the algo is inactive
                return
            
            logger.debug(f"net_vol:{self.net_volume}|total_sell:{self.total_sell},total_buy:{self.total_buy},algo_count: {self.row['user_algo_type_count'][self.username]}")
            if (self.net_volume > 0 and abs(self.total_sell) > abs(self.net_volume)) or (self.net_volume < 0 and abs(self.total_buy) > abs(self.net_volume) ) :
                logger.debug("self.net_volume > 0 and abs(self.total_sell) > abs(self.net_volume)) or (self.net_volume < 0 and abs(self.total_buy) > abs(self.net_volume")
                # self.diaoxia_offset = 'close'
                # self.row['filled_qty'] = self.row['filled_vol']
                self.update_db()
   
            
            self.diaoxia_offset = self.determine_trade_type(self.net_volume,self.row['user_algo_type_count'][self.username])

            revised_qty = int(self.qty) - self.row['filled_vol']
            # logger.debug(f"{self.net_volume}, {self.total_buy}, {self.diaoxia_availability},{self.diaoxia_offset}")
            # Log order book data
            logger.debug(f"{self.username}|{self.algoname}|OKXup:{datetime.fromtimestamp(self.last_update_okx).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}|HTXup:{datetime.fromtimestamp(self.last_update_htx).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} htxside:{self.htx_best_bid}|{self.htx_best_bid_sz}|{self.htx_best_ask}|{self.htx_best_ask_sz} okxside: {self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz} {self.row['user_algo_type_count'][self.username]} ")

            # Precompute spread conditions
            bid_ask_spread_1 = float(self.htx_best_bid) - float(self.best_ask)
            bid_ask_spread_2 = float(self.best_bid) - float(self.htx_best_ask)

            # Determine min available amount for orders
            min_avail_amt_buy = min(int(self.htx_best_bid_sz), int(self.best_ask_sz), 100, revised_qty,1)
            min_avail_amt_sell = min(int(self.best_bid_sz), int(self.htx_best_ask_sz), 100, revised_qty,1)
            okx_update = datetime.fromtimestamp(self.last_update_okx).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            htx_update = datetime.fromtimestamp(self.last_update_htx).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

            # sell htx
            # Check spread conditions for order execution
            if spread > 0 and bid_ask_spread_1 >= spread:
                logger.debug(f"{self.username}|{self.algoname}|OKXup:{okx_update}|HTXup:{htx_update} htxside:{self.htx_best_bid}|{self.htx_best_bid_sz}|{self.htx_best_ask}|{self.htx_best_ask_sz} okxside: {self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz} SPREAD DETECTED Count:{self.check_count} ")

                if self.check_count == self.check_requirement_count:
                    asyncio.gather(
                        self.place_market_order_htx(min_avail_amt_buy,self.lag_direction),
                        self.place_market_order_okx(min_avail_amt_buy,self.lead_direction),
                    )
                    # task_htx = asyncio.create_task(self.place_market_order_htx(min_avail_amt_sell, self.lag_direction))
                    # task_okx = asyncio.create_task(self.place_market_order_okx(min_avail_amt_sell, self.lead_direction))
                    self.row['filled_vol'] += min_avail_amt_buy
                    self.row['user_algo_type_count'][self.username]['diaoxia']['sell'] += 1
                    
                    self.check_count = 0
                else:
                    self.check_count += 1
                    time.sleep(self.call_interval)



            # buy htx
            elif spread < 0 and bid_ask_spread_2 >= abs(spread):
                # logger.debug(f"{self.username}|{self.algoname}|OKXup:{okx_update}|HTXup:{htx_update} htxside:{self.htx_best_bid}|{self.htx_best_bid_sz}|{self.htx_best_ask}|{self.htx_best_ask_sz} okxside: {self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz} SPREAD DETECTED")

                # asyncio.gather(
                #     self.place_market_order_htx(min_avail_amt_sell,self.lag_direction),
                #     self.place_market_order_okx(min_avail_amt_sell,self.lead_direction),
                # )
                # task1 = asyncio.create_task(self.place_market_order_htx(min_avail_amt_sell, self.lag_direction))
                # task2 = asyncio.create_task(self.place_market_order_okx(min_avail_amt_sell, self.lead_direction))

                # self.row['filled_vol'] += min_avail_amt_sell
                logger.debug(f"{self.username}|{self.algoname}|OKXup:{okx_update}|HTXup:{htx_update} htxside:{self.htx_best_bid}|{self.htx_best_bid_sz}|{self.htx_best_ask}|{self.htx_best_ask_sz} okxside: {self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz} SPREAD DETECTED Count:{self.check_count} ")
                if self.check_count == self.check_requirement_count:
                  

                    asyncio.gather(
                        self.place_market_order_htx(min_avail_amt_buy,self.lag_direction),
                        self.place_market_order_okx(min_avail_amt_buy,self.lead_direction),
                    )
                    # task_htx = asyncio.create_task(self.place_market_order_htx(min_avail_amt_sell, self.lag_direction))
                    # task_okx = asyncio.create_task(self.place_market_order_okx(min_avail_amt_sell, self.lead_direction))
                    self.row['user_algo_type_count'][self.username]['diaoxia']['buy'] -= 1

                    self.row['filled_vol'] += min_avail_amt_buy

                    self.check_count = 0
                else:
                    self.check_count += 1

                    time.sleep(self.call_interval)
                    
            else:
                self.check_count = 0

            
        except Exception as e:
            self.update_db()
            logger.debug(f"Error occurred in check_condition: {traceback.format_exc}")
            raise e


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
                    # When place order, we need to keep track of id. 
                    # Order will be placed to buy on htx side
                    # spread = float(self.spread)
                    self.limit_buy_price = float(self.best_bid) - float(self.spread)
                    self.limit_buy_size = self.qty
                    
                    self.lead_direction, self.lag_direction = ('buy', 'sell') if float(self.spread) > 0 else ('sell', 'buy')
                    self.last_update_okx = time.time()
                    # if self.row['filled_vol'] < int(self.qty):
                    self.check_condition(float(self.spread),'okx_callback')
                
                
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
                        # total net availabilty is total position. i.e net_availability == 0 means theres no position and for htx, direction will be open
                        self.net_volume = sum(pos['volume'] if pos['direction'] == 'buy' else -pos['volume'] for pos in message['data'])
                        self.total_sell = -(self.row['user_algo_type_count'][self.username]['diaoyu']['sell'] + self.row['user_algo_type_count'][self.username]['diaoxia']['sell'])
                        self.total_buy = self.row['user_algo_type_count'][self.username]['diaoyu']['buy'] + self.row['user_algo_type_count'][self.username]['diaoxia']['buy']
                      
            except Exception as e:
                logger.error(f"Error{traceback.format_exc()}")

    async def place_market_order_htx(self,size,direction):
        # Use limit_buy_price and limit_buy_size directly instead of `self.limit_buy_price`
            try:
                result = await self.place_order_htx_helper(self.htx_tradeapi, self.ccy.replace('-SWAP',''), size, direction,self.diaoxia_offset[direction])
                logger.debug(f"{self.username}|{self.algoname}|OKXup:{datetime.fromtimestamp(self.last_update_okx).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}|HTXup:{datetime.fromtimestamp(self.last_update_htx).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} htxside: {self.htx_best_bid}|{self.htx_best_bid_sz}|{self.htx_best_ask}|{self.htx_best_ask_sz}  okxside: {self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz} {self.row['user_algo_type_count'][self.username]}|{self.diaoxia_availability}|{self.diaoxia_offset[direction]}  htx_place_market_order result:{result}")

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
                    self.check_condition(float(self.spread),'htx_callback')
                  
                    # logger.debug(f"{self.username}|{self.algoname}|HTX BBO:{message}")
                    
                    
            except Exception as e:
                logger.error(f"{self.username}|{self.algoname}| HTX PUBLICCALLBACK:",e)

    async def place_market_order_okx(self,size,direction):
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

            logger.debug(f"{self.username}|{self.algoname}|OKXup:{datetime.fromtimestamp(self.last_update_okx).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}|HTXup:{datetime.fromtimestamp(self.last_update_htx).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} htxside: {self.htx_best_bid}|{self.htx_best_bid_sz}|{self.htx_best_ask}|{self.htx_best_ask_sz}  okxside: {self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz} {self.row['user_algo_type_count'][self.username]}|{self.diaoxia_availability}|{self.diaoxia_offset} |okx_place_order result:{result} ")

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
