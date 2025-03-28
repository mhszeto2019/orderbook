import asyncio
import json
import random
from websockets.exceptions import ConnectionClosedError
from okx.websocket.WsPublicAsync import WsPublicAsync


class OkxBbo:
    def __init__(self, url="wss://ws.okx.com:8443/ws/v5/public"):
        self.url = url
        self.ws = None
        self.subscribed_pairs = []
        self.spread = 100
        self.qty = 1
        self.is_running = False
        self.reconnect_delay = 2  # Start with 2s, increase if failures occur

    async def start(self):
        """Start the WebSocket connection."""
        print("🔌 Initializing WebSocket connection...")
        if self.ws is None:  # Ensure we create a fresh connection
            self.ws = WsPublicAsync(url=self.url)
        await self.ws.start()

    async def subscribe(self, channel, inst_id, callback):
        """Subscribe to a specific channel and instrument ID."""
        arg = {"channel": channel, "instId": inst_id}
        if inst_id not in self.subscribed_pairs:
            self.subscribed_pairs.append(inst_id)
        await self.ws.subscribe([arg], callback)

    async def run(self, channel, currency_pairs, callback):
        """Run the WebSocket client with automatic reconnection."""
        self.is_running = True
        retry_attempts = 0

        while self.is_running:
            try:
                print("🔌 Connecting to WebSocket...")
                await self.start()

                for pair in currency_pairs:
                    await self.subscribe(channel, pair, callback)

                print("✅ Subscribed! Listening for messages...")

                # Simulate a forced disconnection after 10-15 seconds
                asyncio.create_task(self.force_disconnect())

                while self.is_running:
                    await asyncio.sleep(1)  # Keep the connection alive

            except (ConnectionClosedError, asyncio.CancelledError) as e:
                print(f"⚠️ WebSocket disconnected: {e}. Retrying...")
                retry_attempts += 1

            except Exception as e:
                print(f"❌ Unexpected error: {e}. Retrying...")
                retry_attempts += 1

            finally:
                await self.close()
                sleep_time = min(2 ** retry_attempts, 60)  # Exponential backoff
                print(f"🔄 Reconnecting in {sleep_time} seconds...")
                await asyncio.sleep(sleep_time)

                # 💥 Ensure we restart the connection
                self.ws = None  # Force a fresh connection
                print("♻️ Restarting WebSocket connection...")
                
    async def close(self):
        """Close the WebSocket connection properly."""
        if self.ws:
            try:
                await self.ws.factory.close()
                print("🔴 WebSocket connection closed.")
            except Exception as e:
                print(f"⚠️ Error closing WebSocket: {e}")
            finally:
                self.ws = None  # Ensure we fully reset

    def okx_publicCallback(self, message):
        """Callback function to handle incoming messages."""
        try:
            json_data = json.loads(message)
            print(json_data)
        except Exception as e:
            print(f"⚠️ Error processing message: {e}")

    async def force_disconnect(self):
        """Simulate an unexpected WebSocket disconnection."""
        wait_time = random.randint(10, 15)  # Simulate at a random time
        await asyncio.sleep(wait_time)
        print("🔌 Simulating WebSocket disconnection...")
        
        # if self.ws:
        #     await self.ws.factory.close()  # Simulate real disconnection
        #     self.ws = None  # Ensure ws is reset
        print("HELLO FOROCE CONNECTION")
        raise ConnectionClosedError(1000, "Simulated disconnection")  # 💥 Force reconnection


async def main():
    okx_client = OkxBbo()
    await okx_client.run("bbo-tbt", ["BTC-USD-SWAP"], okx_client.okx_publicCallback)


if __name__ == '__main__':
    asyncio.run(main())
