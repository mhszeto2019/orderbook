import redis
import json

# currently not in use
class RedisPublisher:
    def __init__(self, host='localhost', port=6379):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)

    def publish(self, redis_channel, data):
        """Publish data to the specified Redis channel."""
        message = json.dumps(data)  # Convert data to JSON string
        self.redis_client.publish(redis_channel, message)
        print(f"Published message to channel '{redis_channel}': {message}")

# Usage example
if __name__ == "__main__":
    publisher = RedisPublisher()
    # Example data to publish

    for i in range(100):
    # Publish the data to a Redis channel
        data_to_publish = {
            'event': 'order_update',
            'order_id': 12346,
            'status': 'completed'
        }

        publisher.publish('username:example_channel', data_to_publish)
        data_to_publish2 = {
            'event': 'order_update',
            'order_id': 123,
            'status': 'completed'
        }

        publisher.publish('username:example_channel2', data_to_publish2)
