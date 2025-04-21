import asyncio
from okx.websocket.WsPublicAsync import WsPublicAsync
import redis
import json
from datetime import datetime
import os
import json
import configparser
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
# print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)
config_source = 'redis'
REDIS_HOST = config[config_source]['host']
REDIS_PORT = config[config_source]['port']
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


class OKXWebSocketClient:
    def __init__(self, url="wss://wspap.okx.com:8443/ws/v5/public"):
        self.url = url
        self.ws = None
        self.subscribed_pairs = []  # To keep track of subscribed pairs

    async def start(self):
        """Start the WebSocket connection."""
        self.ws = WsPublicAsync(url=self.url)
        await self.ws.start()

    async def subscribe(self, channel, inst_id, callback):
        """Subscribe to a specific channel and instrument ID."""
        arg = {"channel": channel, "instId": inst_id}
        self.subscribed_pairs.append(inst_id)  # Track the subscription
        await self.ws.subscribe([arg], callback)  # Subscribe using the args list

    async def run(self,channel ,currency_pairs, callback):
        """Run the WebSocket client, subscribing to the given currency pairs."""
        await self.start()
        
        # Subscribe to all specified currency pairs
        for pair in currency_pairs:
            await self.subscribe(channel, pair, callback)

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
            await self.ws.unsubscribe(self.subscribed_pairs)

    async def close(self):
        """Close the WebSocket connection."""
        if self.ws:
            await self.ws.close()
            print("WebSocket connection closed.")

    @staticmethod
    def publicCallback(message):
        """Callback function to handle incoming messages."""
        json_data = json.loads(message)
        if json_data.get('data'):
            currency_pair = json_data["arg"]["instId"]
            instrument = 'SPOT'
            if 'SWAP' in currency_pair:
                instrument = 'SWAP'
            channel = json_data["arg"]["channel"]
            redis_key = f'okx:{instrument}:{channel}:{currency_pair}'
            print(redis_key)
            # Prepare a dictionary of the fields to store
            redis_data = {
                "currency": currency_pair,
                "channel": json_data["arg"]["channel"],
                "ask_price": json_data["data"][0]["asks"][0][0],  # Renamed for consistency
                "ask_size": json_data["data"][0]["asks"][0][1],   # Renamed for consistency
                "bid_price": json_data["data"][0]["bids"][0][0],  # Renamed for consistency
                "bid_size": json_data["data"][0]["bids"][0][1],   # Renamed for consistency
                "timestamp": datetime.fromtimestamp(float(json_data["data"][0]["ts"]) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                "sequence_id": json_data["data"][0]["seqId"],
                "exchange":"okx"

            }
            print(redis_data)
            # Store data in Redis
            redis_client.hset(redis_key, mapping=redis_data)
            redis_client.publish(redis_key, json.dumps(redis_data))

            # print("Data stored in Redis.")
            stored_data = redis_client.hgetall(redis_key)
            # print("Stored data in Redis:", stored_data)



# Example usage
async def main():
    client = OKXWebSocketClient()
    # List of currency pairs to subscribe to
    # currency_pairs = ["BTC-USDT","BTC-USDC","BTC-USD-SWAP"]  # Add more pairs as needed
    currency_pairs = ["BTC-USD-SWAP"]  # Add more pairs as needed

    channel = "bbo-tbt"
    await client.run(channel,currency_pairs, client.publicCallback)

if __name__ == '__main__':
    asyncio.run(main())
