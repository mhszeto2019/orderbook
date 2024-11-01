import asyncio
from okx.websocket.WsPublicAsync import WsPublicAsync

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
        print("publicCallback", message)


# Example usage
async def main():
    client = OKXWebSocketClient()
    await client.run("bbo-tbt", "BTC-USD", client.publicCallback)

if __name__ == '__main__':
    asyncio.run(main())
