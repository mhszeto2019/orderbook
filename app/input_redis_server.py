from flask import Flask, request, jsonify
import redis
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configure Redis connection
redis_host = 'localhost'
redis_port = 6379
redis_db = 0  # Default database
r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)

@app.route('/place_order', methods=['POST'])
def place_order():
    # Get the order data from the request
    order_data = request.json

    # Save the order data to Redis
    r.set('order_data_key', json.dumps(order_data))  # Replace 'order_data_key' with your desired key

    # Publish the order data to a Redis channel
    r.publish('order_updates', json.dumps(order_data))

    return jsonify({"status": "success", "message": "Order data updated in Redis."})

@app.route('/get_transaction_history', methods=['GET'])
def get_transaction_history():
    # Fetch transaction history from Redis
    transactions = r.get('order_data_key')
    if transactions:
        return jsonify(json.loads(transactions))
    return jsonify([])  # Return an empty list if no transactions

if __name__ == '__main__':
    app.run(debug=True)
