import redis
import json
import threading

class RedisSubscriber:
    def __init__(self, host='localhost', port=6379):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.subscribed_channel = None
        self.data = None

    def start(self, redis_channel):
        """Start the Redis subscriber."""
        self.subscribed_channel = redis_channel
        self.pubsub.subscribe(**{self.subscribed_channel: self.handle_message})
        print(f"Subscribed to Redis channel: {self.subscribed_channel}")

        # Start listening in a separate thread
        listener_thread = threading.Thread(target=self.listen)
        listener_thread.daemon = True  # Daemon thread will exit when the main program exits
        listener_thread.start()

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
        self.data = order_data
        # print(self.data)

    def get_data(self):
        """Getter method to access the latest data."""
        return self.data
