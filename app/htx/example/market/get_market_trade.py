from huobi.client.market import MarketClient
from huobi.utils import *
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

market_client = MarketClient()
list_obj = market_client.get_market_trade(symbol="eosusdt")
LogInfo.output_list(list_obj)
