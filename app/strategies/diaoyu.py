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

from app.strategies.connection_helper import OkxBbo,HtxPositions

# for DiaoYu, positive spread means buying on HTX and selling on OKX while negative spread means selling on HTX and buying on OKX. The concept of a lead and lag exchange doesnt apply here because diaoyu's mechanism is fixed to making a limit order on htx and a market order on okx 

    
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
        self.row['order_id'] = None
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
        self.lock = threading.Lock()

    async def revoke_order_by_id(self):
        # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",self.htx_apikey,self.htx_secretkey)
        try:
            with self.lock:
                try:
                    tradeApi = self.htx_tradeapi

                    revoke_orders = await tradeApi.revoke_order(self.ccy,
                                            body = {
                                            "order_id":self.row['order_id'] ,
                                            "contract_code": self.ccy.replace('-SWAP','')
                                            }
                                        )
                    
                    # logger.debug(f"{self.username}|{self.algotype}|{self.algoname}|revoke_order:{revoke_orders.get('data',[])}")

                    self.row['order_id']  = None

                except Exception as e:
                    logger.debug(f"{self.username}|{self.algotype}|{self.algoname}|Revoke Order not successful :{revoke_orders}")

        except Exception as e:
            logger.error(f"{self.username}|{self.algotype}|{self.algoname}|REVOKE ORDER ERROR:{e}")

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
        # for future
        notification_futures_url = 'wss://api.hbdm.com'
        notification_futures_endpoint = '/notification'
        
        notification_subs = [
            {
                "op": "sub",
                "cid": str(uuid.uuid1()),
                "topic": "matchOrders.BTC-USD"
            }
        ]
        notification_futures_subs = [
            {
                "op": "sub",
                "cid": str(uuid.uuid1()),
                "topic": "matchOrders.*"
            }
        ]
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
        # logger.debug('close HTX')
        self.revoke_order_by_id()
        self.update_db()
    
    def okx_publicCallback(self,message):
        try:
            """Callback function to handle incoming messages."""
            json_data = json.loads(message)
            if json_data.get('data'):
                currency_pair = json_data["arg"]["instId"]
            
                self.best_bid = json_data["data"][0]["bids"][0][0]
                self.best_bid_sz = json_data["data"][0]["bids"][0][1]
                self.best_ask = json_data["data"][0]["asks"][0][0]
                self.best_ask_sz = json_data["data"][0]["asks"][0][1]
                # Place limit order on lagging party e.g htx - htx requires cancel and place new order for amend
                # When place order, we need to keep track of id. 
                # Order will be placed to buy on htx side
                self.limit_buy_price = float(self.best_bid) - float(self.spread)
                self.limit_buy_size = self.qty
                limit_buy_price = float(self.best_bid) - float(self.spread)
                limit_ask_price = float(self.best_ask) - float(self.spread)
                limit_qty = self.qty
                
                if int(self.spread) < 0:
                    htx_direction = 'sell'
                    okx_direction = 'buy'
                else:
                    htx_direction = 'buy'
                    okx_direction = 'sell'
                
                best_bid = json_data["data"][0]["bids"][0][0]
                best_ask = json_data['data'][0]['asks'][0][0]
                # Throttle: Ensure minimum interval between API calls
                current_time = time.time()
                if current_time - self.last_call_time >= self.call_interval:
                    self.last_call_time = current_time

                    if self.row['state']:
                      
                        if htx_direction == 'sell':
                            
                            asyncio.create_task(self.place_limit_order_htx(self.algoname, best_bid,limit_buy_price, limit_qty,htx_direction,okx_direction))
                        elif htx_direction == 'buy':
                            asyncio.create_task(self.place_limit_order_htx(self.algoname, best_ask,limit_ask_price, limit_qty,htx_direction,okx_direction))
                    else:
                        if self.row['order_id'] :
                            asyncio.create_task(self.revoke_order_by_id())
                        # self.row['order_id']  = None
                logger.debug(f"{self.username}|{self.algotype}|{self.algoname}|OKX BBO:{json_data}")
                
        except Exception as e:
            logger.error(f"{self.username}|{self.algotype}|{self.algoname}|OKX PUBLICCALLBACK ERROR:{e}")

    async def limit_order_function(self,limit_buy_price,limit_buy_size,htx_direction):
        
        try:
            result = None
            positions = await self.htx_tradeapi.get_positions(self.ccy,body = {
                "symbol": "BTC"
                }
                )
            position_data = positions.get('data', [])
            # Check if position_data has at least one item to avoid IndexError 
            # If there is a position, we need to find out these conditions:
                #1) limit_size left for our new order which is called availability
                #2) limit size required to close existing opposite direction called closing size
            # If there is position, prioritise on closing first

            closing_size = 0
            availability = int(limit_buy_size)
            opposite_direction = "sell" if htx_direction == "buy" else "buy"
            net_pos_size = 0

            if position_data:
                # finding how many vol to close and how mnay available to increase position
                # if len(position_data) > 1:
                for pos in position_data:
                    pos_vol = int(pos['volume'])
                    # pos_vol = int(pos['available'])
                    # closing size
                    if pos['direction'] != htx_direction:
                        availability -= pos_vol
                        closing_size += pos_vol
                        net_pos_size -= pos_vol
                    else:
                        net_pos_size += pos_vol                        
          
            # else:
            #     # If no position data is found, set defaults for availability and direction
            #     availability = 0
            #     direction = None

            # logger.debug(f'availability{availability}')
            # logger.debug(f'direction{pos['direction']}')        
            # logger.debug(f'closing_size{closing_size}')            

            # If we dont need to close, we just open a position
            if closing_size == 0:
                # same direction so we just add on
                result = await self.htx_tradeapi.create_swap_orders(self.ccy,body = [{
                "contract_code": self.ccy.replace('-SWAP',''),
                "price": limit_buy_price,
                "created_at": str(datetime.datetime.now()),
                "volume": str(availability),
                "direction": htx_direction,
                "offset": "open",
                "lever_rate": 5,
                "order_price_type": "limit"       
                }]
                )
                # logger.debug(f"Result{result}")
                self.row['order_id']  = result['data'][0]['ordId']


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
                    # logger.debug(f"Result{result}")

                    self.row['order_id']  = result['data'][0]['ordId']

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
                    self.row['order_id']  = result['data'][0]['ordId']
                         
            # logger.debug(f"{self.username}|{self.algotype}|{self.algoname}|{result} (Limit Order function)")
            
        except Exception as e:
            logger.error(f"LIMIT ORDER FUNCTION ERROR:{e}")

        return result

    async def place_limit_order_htx(self,algoname, best_bid,limit_buy_price, limit_buy_size,htx_direction,okx_direction):
        # Use limit_buy_price and limit_buy_size directly instead of `self.limit_buy_price`
        if self.row['state']:
            try:
                with self.lock:
                    # async with asyncio.Lock():
                    self.row['okx_direction'] = okx_direction
                    # Check if theres is an order_id. if dont have, it will be a new order
                    if self.row['order_id']:
                        # If there is an order id present , we revoke it 
                        revoke_orders = await self.htx_tradeapi.revoke_order(self.ccy,
                            body = {
                            "order_id":self.row['order_id'] ,
                            "contract_code": self.ccy.replace('-SWAP','')
                            }
                        )
                        revoke_order_data = revoke_orders.get('data', [])
                        self.row['order_id']  = None

                        # logger.debug(f"{self.username}|{self.algotype}|{self.algoname}|{revoke_order_data}(Revoke order data with order_id and True)")
                        # Upon successful revoking, we place an order
                        if len(revoke_order_data['errors']) == 0:
                            # Call the asynchronous place_order function
                            result = await self.limit_order_function(limit_buy_price,limit_buy_size,htx_direction)
                            self.row['order_id']  = result['data'][0]['ordId']

                        else:
                            # self.row['order_id']  = None
                            # logger.debug(f"{self.username}|{self.algotype}|{self.algoname}|{revoke_order_data}(Revoke order data with order_id and True ERROR)")
                            # If revoke order has an error, there will be 
                            # 2 scenarios can be present here:
                            # 1) when qty_filled matches the desired amount set by trader
                            if self.htx_is_filled or self.limit_qty == self.htx_filled_volume:
                                self.row['state'] = False
                                # Reset values after fill
                                self.htx_is_filled = False
                                self.htx_filled_volume = 0 
                                self.update_db()
                                self.row['order_id']  = None
                            # 2) when qty_filled doesnt match the desired amount
                            else:
                                self.row['order_id']  = None
                                # Continue to place limit order since qty has not been filled
                                result = await self.limit_order_function(limit_buy_price,limit_buy_size,htx_direction)
                                self.row['order_id']  = result['data'][0]['ordId']
                            logger.debug(f"{self.username}|{self.algotype}|{self.algoname}|{self.row['order_id']}(Revoke order data selforderid presented)")
                                        
                    else:
                        result = await self.limit_order_function(limit_buy_price,limit_buy_size,htx_direction)
                        self.row['order_id']  = result['data'][0]['ordId']
                    # return
                    if result:
                        logger.debug(f"{self.username}|{self.algotype}|{self.algoname}|{result}()")

            except Exception as e:
                logger.error(f"{self.username}|{self.algotype}|{self.algoname}| PLACE LIMIT ORDER ERROR:{e}")
                
    def htx_publicCallback(self,message):
        try:
            with self.lock:
                trade = message.get('trade',[])
                match_order_id = message.get('order_id','no order id yet')
            
                # logger.debug(message)
                if trade and message['status'] in [4,5,6] and self.row['order_id']  == message['order_id']:

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
                        # If the loop is already running, create a new task
                        asyncio.create_task(self.place_market_order_okx(self.row['filled_volume'],match_order_id))
                    else:
                        # Run the async function to completion in the current thread
                        loop.run_until_complete(self.place_market_order_okx(self.row['filled_volume'],match_order_id))
                    logger.debug(f"{self.username}|{self.algotype}|{self.algoname}|htx position result:{trade}")
                    
        except Exception as e:
            logger.error(f"{self.username}|{self.algotype}|{self.algoname}| HTX PUBLICCALLBACK:{e}")

    async def place_market_order_okx(self,filled_volume,match_order_id):
        try:
            with self.lock:
                # Initialize TradeAPI
                tradeApi = self.okx_tradeapi
                result = tradeApi.place_order(
                    instId= 'BTC-USD-SWAP',
                    tdMode= "cross", 
                    side= self.row['okx_direction'], 
                    posSide= '', 
                    ordType= 'market',
                    sz= filled_volume
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
                        self.row['order_id']  = match_order_id

                    self.row['order_id']  = None

                else:
                    result['data'][0]['sCode'] = 400
                    logger.debug('OKX MARKET TRADE FAILED')

                logger.debug(f"{self.username}|{self.algotype}|{self.algoname}|okx_place_order result:{result}")

                return result
        except Exception as e:
            logger.error(f"{self.username}|{self.algotype}|{self.algoname}|okx_place_order ERROR:{e}")
    
    def update_db(self):
        # Input should be unique so it should be username,algo_type and algoname
        # Update based on parameters. by updating here it will trigger the algo listener
        try:
           
            query = "update algo_dets set state = false where username = %s and algo_type=%s and  algo_name=%s"
            self.cursor.connection.commit()
            with self.cursor.connection.cursor() as cursor:
                cursor.execute(query, (self.username, self.algotype, self.algoname))
                self.cursor.connection.commit()
            # https://stackoverflow.com/questions/64995178/decryption-failed-or-bad-record-mac-in-multiprocessing
            logger.debug(f"{self.username}|{self.algotype}|{self.algoname}|Database Updated")
        
        except Exception as e:
            logger.error(f"{self.username}|{self.algotype}|{self.algoname}|DATABASE Error:{e}")
        # finally:
        #     self.cursor.close()  # Close the cursor
            # return 
        

if __name__ == '__main__':
    # 1 strat = 1 algo 
    try:
        print('try start')
          # strat.start_clients()
    except KeyboardInterrupt:
        print("Stopping clients...")
        # strat.stop_clients()
