import redis
import json
import asyncio
import websockets


class RedisPublisher:
    def __init__(self, host='localhost', port=6379):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)

    def publish(self, redis_channel, data):
        """Publish data to the specified Redis channel."""
        message = json.dumps(data)  # Convert data to JSON string
        self.redis_client.publish(redis_channel, message)
        print(f"Published message to channel '{redis_channel}': {message}")



# Redis Subscriber class to connect to Redis and subscribe to a channel
class RedisSubscriber:
    def __init__(self, host='localhost', port=6379):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)

    def subscribe(self, redis_channel):
        """Subscribe to the given Redis channel and forward messages to WebSocket clients."""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(redis_channel)

        return pubsub

    def listen_to_redis(self, pubsub, websocket):
        """Listen to Redis messages and send them to WebSocket."""
        for message in pubsub.listen():
            if message['type'] == 'message':
                # Send the Redis message to the WebSocket client
                websocket.send(message['data'])

# WebSocket handler to manage browser connections
async def websocket_handler(websocket):
    redis_subscriber = RedisSubscriber()

    # Subscribe to the Redis channel
    pubsub = redis_subscriber.subscribe('my_channel')

    # Start listening for Redis messages and forward them to the WebSocket client
    while True:
        # Redis messages will be forwarded here
        await redis_subscriber.listen_to_redis(pubsub, websocket)

# Start the WebSocket server
async def main():
    # websockets.serve requires the handler and address (host, port)
    server = await websockets.serve(websocket_handler, "localhost", 8765)
    print("WebSocket server is running on ws://localhost:8765")
    await server.wait_closed()

# Run the event loop
if __name__ == "__main__":
    asyncio.run(main())
