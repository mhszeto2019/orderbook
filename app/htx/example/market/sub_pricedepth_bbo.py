import signal
from huobi.client.market import MarketClient
from huobi.exception.huobi_api_exception import HuobiApiException
from huobi.model.market import PriceDepthBboEvent

def callback(price_depth_event: 'PriceDepthBboEvent'):
  
    # price_depth_event.print_object()
    print(price_depth_event.tick.ask)
    # print(price_depth_event.tick.askSize)
    # print(price_depth_event.tick.bid)
    # print(price_depth_event.tick.bidSize)
    # print(price_depth_event.tick.quoteTime)
    # print(price_depth_event.tick.symbol)


def error(e: 'HuobiApiException'):
    print(e.error_code + e.error_message)

# Initialize the MarketClient
market_client = MarketClient()

# Subscribe to the WebSocket
market_client.sub_pricedepth_bbo("btcusdswap", callback, error)
# market_client.sub_pricedepth_bbo("ethusdt", callback, error)


# # Function to handle shutdown
def shutdown_handler(signum, frame):
    print("Shutting down gracefully...")
    # market_client.unsubscribe_all()  # Unsubscribe from all WebSocket streams
    exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

try:
    while True:
        pass
except (KeyboardInterrupt, SystemExit):
    shutdown_handler()
