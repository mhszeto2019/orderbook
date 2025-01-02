import asyncio
from okx.websocket.WsPublicAsync import WsPublicAsync
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

class OKXWebSocketClient:
    def __init__(self, url="wss://wspap.okx.com:8443/ws/v5/public"):
        self.url = url
        self.ws = None
        self.args = []
        
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
            await self.ws.unsubscribe(self.args, self.publicCallback)

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

            redis_key = f"okxbbo:{currency_pair}"
            print(redis_key)
            # Prepare a dictionary of the fields to store
            redis_data = {
            "currency":currency_pair,
            "channel": json_data["arg"]["channel"],
            "ask_price": json_data["data"][0]["asks"][0][0],  # Renamed for consistency
            "ask_size": json_data["data"][0]["asks"][0][1],   # Renamed for consistency
            "bid_price": json_data["data"][0]["bids"][0][0],  # Renamed for consistency
            "bid_size": json_data["data"][0]["bids"][0][1],   # Renamed for consistency
            "timestamp": json_data["data"][0]["ts"],
            "sequence_id": json_data["data"][0]["seqId"]
            }   

            print(redis_data)
            # "ask_additional_info": json_data["data"][0]["asks"][0][2:],  # Renamed for consistency

            # redis_data = json.dumps(redis_data)
            redis_client.hset(redis_key, mapping=redis_data)
            print("Data stored in Redis.")
            stored_data = redis_client.hgetall(redis_key)
            print("Stored data in Redis:", stored_data)
            print("publicCallback", message)

# Example usage
async def main():
    client = OKXWebSocketClient()
    await client.run("bbo-tbt", "BTC-USDC", client.publicCallback)

if __name__ == '__main__':
    asyncio.run(main())



