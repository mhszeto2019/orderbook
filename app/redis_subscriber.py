# import redis
# import json

# # Configure Redis connection
# redis_host = 'localhost'
# redis_port = 6379
# redis_db = 0  # Default database
# r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)

# # Function to handle incoming messages
# def handle_message(message):
#     data = json.loads(message['data'])
#     print("Received order update:", data)
#     # Here you can update your application state or trigger other actions

# # Subscribe to the 'order_updates' channel
# pubsub = r.pubsub()
# pubsub.subscribe(**{'order_updates': handle_message})

# print("Listening for order updates...")

# # Listen for messages in a loop
# try:
#     for message in pubsub.listen():
#         if message['type'] == 'message':
#             handle_message(message)
# except KeyboardInterrupt:
#     print("Unsubscribing and exiting...")
#     pubsub.unsubscribe()
#     pubsub.close()

import redis 
import json
class RedisSubscriber:
    def __init__(self, host='localhost', port=6379):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.subscribed_channel = 'order_updates'

    def start(self):
        """Start the Redis subscriber."""
        self.pubsub.subscribe(**{self.subscribed_channel: self.handle_message})
        print(f"Subscribed to Redis channel: {self.subscribed_channel}")

        # Listen for messages
        self.listen()

    def listen(self):
        """Listen for messages on the subscribed channel."""
        try:
            for message in self.pubsub.listen():
                if message['type'] == 'message':
                    self.handle_message(message)
        except Exception as e:
            print(f"Error while listening to Redis: {e}")

    def handle_message(self, message):
        """Handle incoming messages from Redis."""
        order_data = json.loads(message['data'])
        print("Received order update from Redis:", order_data)


def run_redis_subscriber():
    redis_subscriber = RedisSubscriber()
    redis_subscriber.start()
