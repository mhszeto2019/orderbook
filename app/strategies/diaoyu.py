import datetime
import uuid
import json
import threading
import asyncio
import time
import sys
import urllib.parse
import hmac
import base64
import hashlib
import gzip
import websockets
import traceback
sys.path.append('/var/www/html/orderbook/htx2')
sys.path.append('/var/www/html/orderbook/htx2/alpha')
# from app.trading_engines.htxTradeFuturesApp import place_limit_contract_order
from app.htx2.HtxOrderClass import HuobiCoinFutureRestTradeAPI
from okx import Trade
import select
import os
# import psycopg2
from okx.websocket.WsPublicAsync import WsPublicAsync
import redis
import configparser
# import decimal
from websockets.exceptions import ConnectionClosedError

# Logger 
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
logger = logging.getLogger('Diaoyu')
logger.setLevel(logging.DEBUG)  # Set log level
# Add the file handler to the logger
logger.addHandler(file_handler)


# CONFIG
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
import psycopg2
import configparser
import os
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
config.read(config_file_path)


# Database configuration
DB_CONFIG = {
    "dbname": dbname,
    "user": dbusername,
    "password": dbpassword,
    "host": "localhost",
    "port": 5432
}


from app.strategies.connection_helper_diaoyu import OkxBbo,HtxPositions

# for DiaoYu, positive spread means buying on HTX and selling on OKX while negative spread means selling on HTX and buying on OKX. The concept of a lead and lag exchange doesnt apply here because diaoyu's mechanism is fixed to making a limit order on htx and a market order on okx 
from collections import deque
    
class Diaoyu:
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
        self.limit_ask_price = None
        self.order_id = None
        self.htx_direction = None
        self.okx_direction = None
        self.received_data = None  # Variable to store received data

        # status
        self.htx_filled_volume = 0
        self.htx_is_filled = False

        # db connection
        self.cursor = cursor
        
        # throttle
        self.last_call_time = 0
        self.call_interval = 1

        # lock for race conditions
        self.lock = threading.RLock()
        self.connect_db()
        # self.active_orders = {}
        # self.recently_removed_orders = deque()
        self.order_queue = deque()

        self.last_update_okx = time.time()
        # Time to keep an order in the recently_removed_orders deque (in seconds)
        self.GRACE_PERIOD = 10
        self.revoke_reattempt = 5


    async def revoke_order_by_id(self):
        """Move an order to the recently removed queue instead of deleting immediately."""

        if not self.order_queue:
            # print("⚠️ No orders to cancel")
            return True
        self.order_id = self.order_queue[0]  # Peek at the oldest order

        try:
            tradeApi = self.htx_tradeapi
            revoke_orders = await tradeApi.revoke_order(self.ccy,
                                    body = {
                                    "order_id":self.order_id ,
                                    "contract_code": self.ccy.replace('-SWAP','')
                                    }
                                )

            if 'status' in revoke_orders:
                self.order_queue.popleft()  # Remove from queue
                return True
            # self.order_id = None
            # print(revoke_orders)
            # if revoke_orders and revoke_orders['err_code']:
            #     logger.error("REVOKE ORDER ERROR")

            # logger.debug(f"{self.username}|{self.algotype}|{self.algoname}| htxside:{self.limit_buy_price}|{self.limit_buy_size}|{self.limit_ask_price}|{self.limit_buy_size}  okxside:{self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz} order id:{self.order_id}  |Revoke order result:{revoke_orders}")
            # logger.debug(revoke_orders['data']['errors'][0]['err_code'])
            # if ('status' not in revoke_orders) or (revoke_orders['data']['errors'][0]['err_code']):
            #     logger.debug(f'error detcethed {self.order_id}')
            #     if self.revoke_reattempt > 0 :
            #         logger.debug(f'revoke reattempt,{self.revoke_reattempt}')
            #         self.revoke_order_by_id()
            #         self.revoke_reattempt -= 1
            #     else: 
            #         logger.error(f"Revoke unsucessful after multiple attempts")
            #         return False 
            # else:
            #     return True

        except Exception as e:
            logger.error(f"{self.username}|{self.algotype}|{self.algoname}|Revoke Order not successful :{traceback.format_exc()}")
            self.revoke_order_by_id()

        # return True            


    # connection with okx bbo
    async def run_okx_bbo(self):
        """Run the OkxBbo WebSocket client."""
        self.row['okx_client'] = OkxBbo()
        currency_pairs = ["BTC-USD-SWAP"]  # Add more pairs as needed
        channel = "bbo-tbt"
        await self.row['okx_client'].run(channel, currency_pairs, self.okx_publicCallback)

    # connection with htx positions and orders
    def run_htx_positions(self):
        """Run the HtxPositions WebSocket client."""
        # access_key = 
        # secret_key = 
        access_key = self.htx_apikey
        secret_key = self.htx_secretkey
        # for swaps
        notification_url = 'wss://api.hbdm.com'
        notification_endpoint = '/swap-notification'
        # for futures
        # notification_futures_url = 'wss://api.hbdm.com'
        # notification_futures_endpoint = '/notification'
        
        notification_subs = [
            {
                "op": "sub",
                "cid": str(uuid.uuid1()),
                "topic": "matchOrders.BTC-USD"
            }
        ]
        # notification_futures_subs = [
        #     {
        #         "op": "sub",
        #         "cid": str(uuid.uuid1()),
        #         "topic": "matchOrders.*"
        #     }
        # ]
        # swap client
     
        ws_client = HtxPositions(notification_url, notification_endpoint, access_key, secret_key)
        self.htx_client = ws_client
        ws_client.start(notification_subs, auth=True, callback=self.htx_publicCallback)

    def start_clients(self):
        """Start both WebSocket clients."""
        # Start Htx match orders with positions in a separate thread
        self.htx_thread = threading.Thread(target=self.run_htx_positions, daemon=True)
        self.htx_thread.daemon = True
        self.htx_thread.start()
        # Run OkxBbo in the main asyncio event loop
        asyncio.run(self.run_okx_bbo())
        
    def stop_clients(self):
        """Stop both WebSocket clients gracefully."""
        if self.row['okx_client']:
            # self.okx_client.unsubscribe()  # Assuming the OkxBbo class has a stop method
            # self.okx_client.close()  # Assuming the OkxBbo class has a stop method
            self.row['okx_client'].close()
            self.row['okx_client'].unsubscribe()
            logger.debug(f"{self.username}|{self.algotype}|{self.algoname}|CLOSE AND UNSUBSCRIBED FROM OKX")
        # if self.htx_thread and self.htx_thread.is_alive():
        # Implement stopping mechanism for HtxPositions if necessary
        # print("HTX thread will automatically close because Daemon is set to True ")
        self.revoke_order_by_id()
        self.update_db()
    
    def okx_publicCallback(self,message):
        if not self.row['state']:
            if self.order_id :
                asyncio.create_task(self.revoke_order_by_id())
            return 
        try:
            """Callback function to handle incoming messages."""
            json_data = json.loads(message)
            if json_data.get('data'):
                currency_pair = json_data["arg"]["instId"]
      
                best_bid = json_data["data"][0]["bids"][0][0]
                best_ask = json_data["data"][0]["asks"][0][0]
                # Convert to float only if valid (not None or empty)
                self.best_bid = float(best_bid) if best_bid and best_bid.replace('.', '', 1).isdigit() else None
                self.best_ask = float(best_ask) if best_ask and best_ask.replace('.', '', 1).isdigit() else None
                # Handle missing or invalid values
                if self.best_bid is None or self.best_ask is None:
                    logger.error(f"Invalid best_bid ({best_bid}) or best_ask ({best_ask}) received.")
                    return  # Exit early to prevent errors
                
                self.best_bid_sz = json_data["data"][0]["bids"][0][1]
                self.best_ask_sz = json_data["data"][0]["asks"][0][1]

                # Calculate limit order prices safely
                self.limit_buy_price = self.best_ask - float(self.spread)
                self.limit_buy_size = self.qty
                self.limit_ask_price = self.best_bid - float(self.spread)
                self.last_update_okx = time.time()
                

                # Set up a dictionary for direction mapping and prices
                direction_mapping = {
                    'sell': ('buy', self.limit_buy_price, self.best_bid),
                    'buy': ('sell', self.limit_ask_price, self.best_ask)
                }
                current_time = time.time()

                if current_time - self.last_update_okx > 1:
                    print("TIME DELAYED")
                    logger.debug("Warning: Order book data is stale!")
                    return 

                # Throttle check
                if current_time - self.last_call_time >= self.call_interval:
                    self.last_call_time = current_time

                    # Determine htx_direction based on spread and fetch corresponding values
                    htx_direction = 'sell' if int(self.spread) < 0 else 'buy'
                    okx_direction, limit_price, reference_price = direction_mapping[htx_direction]

                    logger.debug(self.order_queue)
                    asyncio.create_task(self.update_order(self.algoname,
                        reference_price,
                        limit_price,
                        self.qty,
                        htx_direction,
                        okx_direction))


                # Log information in a clean format
                logger.debug(f"{self.username}|{self.algotype}|{self.algoname}| htxlimits: {self.limit_buy_price}|{self.limit_buy_size}|{self.limit_ask_price}|{self.limit_buy_size} okxside: {self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz}")


        except Exception as e:
            logger.error("SWITCH OFF ALL ALGOS!")
            self.update_db()
            logger.error(f"{self.username}|{self.algotype}|{self.algoname}|OKX PUBLICCALLBACK ERROR:{e}")

    async def update_order(self,algoname,best_bid,limit_buy_price,limit_buy_size,htx_direction,okx_direction):
        logger.debug(f"UPDATING ORDER {self.order_queue}")
        if len(self.order_queue) <= 1:
            result = await self.revoke_order_by_id()
            logger.debug(f"RESULT {result}")

            await self.place_limit_order_htx(algoname,best_bid,limit_buy_price,limit_buy_size,htx_direction,okx_direction)



    async def limit_order_function(self,limit_buy_price,limit_buy_size,htx_direction):
        with self.lock:
            try:
                # print(limit_buy_price,limit_buy_size,htx_direction)

                result = None
                positions = await self.htx_tradeapi.get_positions(self.ccy,body = {
                    "symbol": "BTC"
                    }
                    )
                
                position_data = positions.get('data', []) if positions else []
                # Check if position_data has at least one item to avoid IndexError 
                # If there is a position, we need to find out these conditions:
                    #1) limit_size left for our new order which is called availability
                    #2) limit size required to close existing opposite direction called closing size
                # If there is position, prioritise on closing first


                closing_size = 0
                availability = int(limit_buy_size)
                net_pos_size = 0

                if position_data:
                    # finding how many vol to close and how mnay available to increase position
                    # if len(position_data) > 1:
                    for pos in position_data:
                        pos_vol = int(pos['volume'])
                        # we need to check the amount of availability
                        # pos_vol = int(pos['available'])

                        # closing size
                        if pos['direction'] != htx_direction:
                            availability -= pos_vol
                            closing_size += pos_vol
                            net_pos_size -= pos_vol
                        else:
                            net_pos_size += pos_vol                        
            
                # If we dont need to close, we just open a position
                if closing_size == 0:
                    # same direction so we just add on
                    result = await self.htx_tradeapi.create_swap_orders(self.ccy,body = [{
                    "contract_code": self.ccy.replace('-SWAP',''),
                    "price": limit_buy_price,
                    "created_at": str(datetime.datetime.now()),
                    "volume": limit_buy_size,
                    "direction": htx_direction,
                    "offset": "open",
                    "lever_rate": 5,
                    "order_price_type": "limit"       
                    }]
                    )
                    # self.order_id  = result['data'][0]['ordId']
                    # self.place_order(result['data'][0]['ordId'],result)
                    self.order_queue.append(result['data'][0]['ordId'])

                # if cancellation is involved
                else: 

                    #If there is a position that we need to close and there is availability to increase in another direction
                    if int(closing_size) >= int(limit_buy_size):
                        # If there is position that can be closed and there are no more excess positions to carry on
                        # When there is a position  we need to close but no more availability to increase pos
                        result = await self.htx_tradeapi.create_swap_orders(self.ccy.replace('-SWAP',''),body = [{
                        "contract_code": self.ccy.replace('-SWAP',''),
                        "price": limit_buy_price,
                        "created_at": str(datetime.datetime.now()),
                        "volume": str(limit_buy_size),
                        "direction": htx_direction,
                        "offset": "close",
                        "lever_rate": 5,
                        "order_price_type":"limit"
                        }]
                        )
                        # self.order_id  = result['data'][0]['ordId'] if result else None
                        # self.place_order(result['data'][0]['ordId'],result)
                        self.order_queue.append(result['data'][0]['ordId'])

                    else:
                        # if there is position that can be closed and there are no more excess positions to carry on
                        # when theres pos we need to close but no more availability to increase pos
                        result = await self.htx_tradeapi.create_swap_orders(self.ccy.replace('-SWAP',''),body = [{
                        "contract_code": self.ccy.replace('-SWAP',''),
                        "price": limit_buy_price,
                        "created_at": str(datetime.datetime.now()),
                        "volume": str(limit_buy_size),
                        "direction": htx_direction,
                        "offset": "close",
                        "lever_rate": 5,
                        "order_price_type":"limit"
                        }]
                        )
                        # logger.debug(f"Result{result}")
                        # self.order_id  = result['data'][0]['ordId']
                        # self.place_order(result['data'][0]['ordId'],result)
                        self.order_queue.append(result['data'][0]['ordId'])

                
                logger.debug(f"{self.username}|{self.algotype}|{self.algoname}|{result} (Limit Order function)")
                
            except Exception as e:
                # asyncio.create_task(self.revoke_order_by_id())
                logger.error(position_data)
                logger.error(f"LIMIT ORDER FUNCTION ERROR:{traceback.format_exc()}")
                self.update_db()
                # raise Exception
            finally:
                return result



    async def place_limit_order_htx(self, algoname, best_bid, limit_buy_price, limit_buy_size, htx_direction, okx_direction):
        with self.lock:
            result = None
            try:
                self.row['okx_direction'] = okx_direction
                result = await self.limit_order_function(limit_buy_price, limit_buy_size, htx_direction)
                self.order_id = result['data'][0]['ordId']
                logger.debug(f"{self.username}|{self.algotype}|{self.algoname}| New order placed: {self.order_id}")
            except Exception as e:
                logger.error(f"Place Limit order htx:{traceback.format_exc()}")

                
    def htx_publicCallback(self,message):
        if not self.row['state']:
            return 
        with self.lock:
            try:
                trade = message.get('trade',[])
                match_order_id = message.get('order_id','no order id yet')
                logger.debug(f"{self.username}|{self.algotype}|{self.algoname}| self.order id:{self.order_id} | match order id:{match_order_id}")
   
                # Check if there is matched orders but since all algos are listening to the same match order, we need something to differentiate or something to uniquely identify the match order with the order 
                if trade and message['status'] in [4,5,6] and self.order_id  == message['order_id']:
                # if trade and message['status'] in [4,5,6] and (self.order_id in self.active_orders or self.order_id in self.recently_removed_orders):
                    
                    # volume that is filled in this trade
                    self.row['filled_volume'] = message['trade'][0]['trade_volume']
                    # we need to add volume of this trade into total volume filled for htx
                    self.htx_filled_volume += self.row['filled_volume']

                    # the quantity that we want to buy or sell
                    total_limit_buy_size = self.limit_buy_size
                    total_limit_buy_size_int = int(total_limit_buy_size)

                    self.htx_is_filled = self.htx_filled_volume == total_limit_buy_size_int
                    # When order_id that was placed matches with htx position matched order, we fire market order on leading side e.g okx
                    # Place market order on okx with filled volume
                    loop = asyncio.get_event_loop()

                    if loop.is_running():
                        logger.debug("FIRING OKX WITH LOOP")
                        # If the loop is already running, create a new task
                        asyncio.create_task(self.place_market_order_okx(self.row['filled_volume'],match_order_id))
                    else:
                        logger.debug("FIRING OKX WITHOUT LOOP")
                        # Run the async function to completion in the current thread
                        loop.run_until_complete(self.place_market_order_okx(self.row['filled_volume'],match_order_id))

                    logger.debug(f"{self.username}|{self.algotype}|{self.algoname}| htxside:{self.limit_buy_price}|{self.limit_buy_size}|{self.limit_ask_price}|{self.limit_buy_size}  okxside:{self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz}|htx order result:{message}|htx position result Matched:{trade}")

            except Exception as e:
                # logger.debug("SWITCH OFF ALL ALGOS!")
                asyncio.create_task(self.revoke_order_by_id())

                self.update_db()
                logger.error(f"{self.username}|{self.algotype}|{self.algoname}| HTX PUBLICCALLBACK:{e}")

    def okx_market_order_helper(self,vol,match_order_id):
        try:
            result = self.okx_tradeapi.place_order(
                        instId= 'BTC-USD-SWAP',
                        tdMode= "cross", 
                        side= self.row['okx_direction'], 
                        posSide= '', 
                        ordType= 'market',
                        sz= vol
                    )
            result['data'][0]['exchange']='okx'
            
            if result["code"] == "0":
            # OKX MARKET ORDER IS SUCCESSFUL
                result['data'][0]['sCode'] = 200

                if self.htx_is_filled:
                    self.row['state'] = False
                    # Reset values after fill
                    self.htx_is_filled = False
                    self.htx_filled_volume = 0 
                    logger.debug('update db b4')
                    self.update_db()
                    logger.debug('update db after')
                
                else:
                    self.order_id  = match_order_id
                    # self.place_order(match_order_id,result)


                self.order_id  = None

            else:
                result['data'][0]['sCode'] = 400
                logger.debug('OKX MARKET TRADE FAILED')
                self.update_db()

            # logger.debug(f"{self.username}|{self.algotype}|{self.algoname}| htxside:{self.limit_buy_price}|{self.limit_buy_size}|{self.limit_ask_price}|{self.limit_buy_size}  okxside:{self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz}")
            logger.debug(f"{self.username}|{self.algotype}|{self.algoname} | htxside:{self.limit_buy_price}|{self.limit_buy_size}|{self.limit_ask_price}|{self.limit_buy_size}  okxside:{self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz}| okx_place_order result:{result}")
            return 
        except Exception as e:
            logger.error(f"Error in okx helper:{traceback.format_exc()}")

    async def place_market_order_okx(self,filled_volume,match_order_id):
        with self.lock:
            try:
                logger.debug(f"filled-volume:{filled_volume}")
                # filled_volume = 980
                batch_size = 1

                for i in range(filled_volume // batch_size):
                    logger.debug(f"Fire {i+1} {batch_size}")
                    self.okx_market_order_helper(batch_size,match_order_id)
                    await asyncio.sleep(1)


                remainder = filled_volume % batch_size
                await asyncio.sleep(1)
                if remainder:
                    logger.debug(f"Fire {filled_volume // batch_size + 1} {remainder}")
                    self.okx_market_order_helper(remainder,match_order_id)


                # Initialize TradeAPI
                # tradeApi = self.okx_tradeapi
                # result = tradeApi.place_order(
                #     instId= 'BTC-USD-SWAP',
                #     tdMode= "cross", 
                #     side= self.row['okx_direction'], 
                #     posSide= '', 
                #     ordType= 'market',
                #     sz= filled_volume
                # )
                # result['data'][0]['exchange']='okx'
                
                # if result["code"] == "0":
                # # OKX MARKET ORDER IS SUCCESSFUL
                #     result['data'][0]['sCode'] = 200

                #     if self.htx_is_filled:
                #         self.row['state'] = False
                #         # Reset values after fill
                #         self.htx_is_filled = False
                #         self.htx_filled_volume = 0 
                #         logger.debug('update db b4')
                #         self.update_db()
                #         logger.debug('update db after')
                    
                #     else:
                #         self.order_id  = match_order_id
                #         self.place_order(match_order_id,result)


                #     self.order_id  = None

                # else:
                #     result['data'][0]['sCode'] = 400
                #     logger.debug('OKX MARKET TRADE FAILED')
                #     self.update_db()

                # # logger.debug(f"{self.username}|{self.algotype}|{self.algoname}| htxside:{self.limit_buy_price}|{self.limit_buy_size}|{self.limit_ask_price}|{self.limit_buy_size}  okxside:{self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz}")
                # logger.debug(f"{self.username}|{self.algotype}|{self.algoname} | htxside:{self.limit_buy_price}|{self.limit_buy_size}|{self.limit_ask_price}|{self.limit_buy_size}  okxside:{self.best_bid}|{self.best_bid_sz}|{self.best_ask}|{self.best_ask_sz}| okx_place_order result:{result}")

                return 
            
            except Exception as e:
                logger.error(f"{self.username}|{self.algotype}|{self.algoname}|okx_place_order ERROR:{traceback.format_exc()}")
                self.update_db()
    


    def connect_db(self):
        """Ensures the database connection is open and initializes the cursor."""
        if self.cursor.connection.closed:
            self.cursor = psycopg2.connect(**DB_CONFIG).cursor()  # Reconnect if closed


    def update_db(self):
        # Input should be unique so it should be username,algo_type and algoname
        # Update based on parameters. by updating here it will trigger the algo listener
        try:
            # logger.debug(self.cursor)
            self.connect_db()

            query = "update algo_dets set state = false where username = %s and algo_type=%s and  algo_name=%s"
            # self.cursor.connection.commit()
            with self.cursor.connection.cursor() as cursor:
                cursor.execute(query, (self.username, self.algotype, self.algoname))
                self.cursor.connection.commit()
            self.cursor.connection.close()
            logger.debug(f"{self.username}|{self.algotype}|{self.algoname}|Database Updated")

        except Exception as e:
            logger.error(f"{self.username}|{self.algotype}|{self.algoname}|DATABASE Error:{traceback.format_exc()}")
        # finally:
        #     self.cursor.connection.close()  # Close the cursor
        #     return 
        

if __name__ == '__main__':
    # 1 strat = 1 algo 
    try:
        print('try start')
          # strat.start_clients()
    except KeyboardInterrupt:
        print("Stopping clients...")
        # strat.stop_clients()