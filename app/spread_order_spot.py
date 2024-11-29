import signal
import asyncio
import threading
from htx.huobi.client.market import MarketClient as HuobiMarketClient
from htx.huobi.exception.huobi_api_exception import HuobiApiException
from htx.huobi.model.market import PriceDepthBboEvent
from okx.websocket.WsPublicAsync import WsPublicAsync
import logging
import logging.config
import yaml  # You need to install PyYAML to use this example
import os
import json

# Define the path to the YAML file
config_path = os.path.join(os.path.dirname(__file__), "../config_folder", "logging.yaml")
print(config_path)
with open(config_path, "r") as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)

# Create a logger instance
logger = logging.getLogger("my_app")

class OKXWebSocketClient:
    def __init__(self, url="wss://wspap.okx.com:8443/ws/v5/public"):
        self.url = url
        self.ws = None
        self.args = []
        self.okx_data = None  # Store the last received data here

    async def start(self):
        """Start the WebSocket connection."""
        self.ws = WsPublicAsync(url=self.url)
        await self.ws.start()

    async def subscribe(self, channel, inst_id, callback):
        """Subscribe to a specific channel and instrument ID."""
        arg = {"channel": channel, "instId": inst_id}
        self.args.append(arg)
        await self.ws.subscribe(self.args, callback)

    async def run(self, channel, inst_id, callback):
        """Run the WebSocket client, subscribing to the given channel."""
        await self.start()
        await self.subscribe(channel, inst_id, callback)

        # Keep the connection alive
        try:
            while True:
                await asyncio.sleep(1)  # Keep the event loop running
        except KeyboardInterrupt:
            print("Disconnecting...")
            await self.unsubscribe()  # Unsubscribe when exiting
        finally:
            await self.close()  # Ensure WebSocket is closed when done

    async def unsubscribe(self):
        """Unsubscribe from all channels."""
        if self.ws:
            print("Unsubscribing from all channels...")
            await self.ws.unsubscribe(self.args, OKXWebSocketClient.publicCallback)

    async def close(self):
        """Close the WebSocket connection."""
        if self.ws:
            await self.ws.close()
            print("WebSocket connection closed.")

    def publicCallback(self, message):
        """Callback function to handle incoming messages."""
        # print("OKX publicCallback", message)
        # {"arg":{"channel":"bbo-tbt","instId":"BTC-USDT"},"data":[{"asks":[["74165.9","0.00001198","0","1"]],"bids":[["74037.2","4.22723227","0","4"]],"ts":"1730367981772","seqId":26213414}]}
        self.okx_data = message  # Store the incoming data for later comparison


# Instantiate Huobi client
huobi_client = HuobiMarketClient()
okx_client = OKXWebSocketClient()

huobi_data = None  # Store the last received Huobi data
from decimal import Decimal
# Comparison logic
def compare_prices(huobi_data, okx_data):
    """Compare prices from Huobi and OKX."""
    # Check if we have valid data from both brokers
    # print(huobi_data,type(huobi_data),okx_data,type(okx_data))
    if huobi_data and okx_data:
        
        huobi_ask,huobi_bid = Decimal(huobi_data[1]),Decimal(huobi_data[3]) # Adjust based on actual data structure
        okx_ask,okx_askSz,okx_bid,okx_bidSz = Decimal(okx_data['data'][0]['asks'][0][0]),Decimal(okx_data['data'][0]['asks'][0][1]),Decimal(okx_data['data'][0]['bids'][0][0]),Decimal(okx_data['data'][0]['bids'][0][1])  # Adjust for OKX data structure
        # print(huobi_ask,huobi_bid,okx_ask,okx_askSz,okx_bid,okx_bidSz)
        # print(Decimal(huobi_ask),Decimal(okx_bid))
        epsilon = 1e-5
        print(huobi_ask,'-',huobi_bid,'-',okx_ask,'-',okx_bid)

        if abs(huobi_ask - okx_bid) < epsilon:
            print("Prices are the same, hold.")
        elif huobi_ask < okx_bid:
            print("Huobi is cheaper, consider buying on HTX and sell on OKX.")
        elif huobi_bid > okx_ask:
            print("OKX is cheaper, consider buying on OKX and sell on HTX.")
        else:
            # print(huobi_ask,'-',huobi_bid,'-',okx_ask,'-',okx_bid)
            # logger.info(huobi_ask,'-',huobi_bid,'-',okx_ask,'-',okx_bid)
            logger.info(f"{huobi_ask} - {huobi_bid} - {okx_ask} - {okx_bid}")
            print('hee')
# Callback for Huobi
def huobi_callback(price_depth_event: PriceDepthBboEvent):
    """Handle the price depth event from Huobi."""
    global huobi_data
    print("Huobi Data:")
    # price_depth_event.print_object()
    # price_depth_event = dict({"ask":price_depth_event.tick.ask,"askSz":price_depth_event.tick.askSize,"bid":price_depth_event.tick.bid,"bid"})
    price_depth_event = [price_depth_event.tick.symbol,price_depth_event.tick.ask,price_depth_event.tick.askSize,price_depth_event.tick.bid,price_depth_event.tick.bidSize,price_depth_event.tick.quoteTime]

    huobi_data = price_depth_event  # Store the latest Huobi data
    compare_prices(huobi_data, json.loads(okx_client.okx_data))  # Compare with OKX data

# Error handling for Huobi
def huobi_error(e: HuobiApiException):
    print(f"Huobi Error: {e.error_code} {e.error_message}")

# Start OKX WebSocket Client
async def run_okx_client():
    await okx_client.run("bbo-tbt", "BTC-USDT", okx_client.publicCallback)

def run_huobi_client():
    """Start the Huobi client subscription."""
    huobi_client.sub_pricedepth_bbo("btcusdt", huobi_callback, huobi_error)

# Function to handle shutdown
def shutdown_handler(signum, frame):
    print("Shutting down gracefully...")
    # Unsubscribe from all WebSocket streams
    asyncio.run(huobi_client.unsubscribe_all())
    asyncio.run(OKXWebSocketClient.unsubscribe())
    exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# Start the event loop for Huobi in a thread
if __name__ == '__main__':
    huobi_thread = threading.Thread(target=run_huobi_client)
    huobi_thread.start()

    # Start the OKX WebSocket client in the main thread
    asyncio.run(run_okx_client())

    # Wait for the Huobi thread to finish (this may block indefinitely)
    huobi_thread.join()
