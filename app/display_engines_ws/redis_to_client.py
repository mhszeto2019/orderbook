import json
import asyncio
import websockets
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RedisClass import RedisSubscriber

# Set to keep track of connected WebSocket clients for both exchanges
clients = {
    'okx': set(),  # Clients connected to OKX WebSocket server
    'htx': set()   # Clients connected to HTX WebSocket server
}

class RedisToWebSocketPublisher:
    def __init__(self, redis_channel, exchange, websocket_server_task):
        # Create a RedisSubscriber instance
        self.redis_subscriber = RedisSubscriber()

        # The WebSocket server task to send data to the connected clients
        self.websocket_server_task = websocket_server_task

        # The exchange to associate with this Redis channel
        self.exchange = exchange

        # Subscribe to the Redis channel for updates related to this exchange
        self.redis_subscriber.start(redis_channel)

    async def publish_to_websocket(self):
        """Publish Redis data to WebSocket clients when new data is available."""
        while True:
            # Fetch the latest data from Redis
            data = self.redis_subscriber.get_data()

            if data:
                # Send data to all connected WebSocket clients for this exchange
                for client in clients[self.exchange]:
                    try:
                        await client.send(json.dumps(data))
                    except Exception as e:
                        print(f"Error sending data to WebSocket client for {self.exchange}: {e}")

            # Sleep for a short time to prevent tight loops (adjust as needed)
            await asyncio.sleep(1)

async def websocket_handler(websocket, path):
    """Handles incoming WebSocket connections."""
    # Determine which exchange the client is connecting to (based on the path)
    exchange = path.strip('/')
    
    if exchange in clients:
        # Register the client for the specific exchange
        clients[exchange].add(websocket)
        print(f"Client connected to {exchange} WebSocket")

    try:
        # Wait until the connection is closed
        await websocket.wait_closed()
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
    finally:
        # Unregister the client when it disconnects
        if exchange in clients:
            clients[exchange].remove(websocket)
            print(f"Client disconnected from {exchange} WebSocket")

async def start_websocket_server():
    """Start WebSocket server that listens for incoming client connections."""
    server = await websockets.serve(websocket_handler, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")
    await server.wait_closed()

async def main():
    """Start the WebSocket server and setup Redis to WebSocket publishers for multiple exchanges."""
    # Start the WebSocket server
    websocket_server_task = asyncio.create_task(start_websocket_server())

    # Set up Redis to WebSocket publishers for multiple exchanges
    exchanges = ['okx', 'htx']
    publishers = []

    # Subscribe to Redis channels for each exchange
    for exchange in exchanges:
        redis_channel = f"{exchange}:SWAP:books5:BTC-USD-SWAP"  # Example channel for each exchange
        redis_to_ws_publisher = RedisToWebSocketPublisher(redis_channel, exchange, websocket_server_task)
        publishers.append(asyncio.create_task(redis_to_ws_publisher.publish_to_websocket()))

    # Run all tasks concurrently
    await asyncio.gather(websocket_server_task, *publishers)

# Run the asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())