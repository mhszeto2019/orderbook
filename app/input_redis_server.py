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
    print(order_data)
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

@app.route('/retrieveokxbbo/<key>', methods=['GET'])
def retrieve_okxbbo(key):
    """Retrieve data from Redis based on the given key."""
    # Get all fields in the hash
    retrieved_data = r.hgetall(key)
    print(retrieved_data)
    if not retrieved_data:
        return jsonify({"error": "Key not found"}), 404
    retrieved_data['currency'] = str(retrieved_data['currency']) if retrieved_data.get('currency') else "Nan"
    
    # Convert list fields from strings back to lists
    retrieved_data['ask_additional_info'] = retrieved_data['ask_additional_info'].split(',') if retrieved_data.get('ask_additional_info') else []
    retrieved_data['bid_additional_info'] = retrieved_data['bid_additional_info'].split(',') if retrieved_data.get('bid_additional_info') else []

    # Convert numeric fields from strings to their appropriate types
    retrieved_data['ask_size'] = float(retrieved_data['ask_size']) if retrieved_data.get('ask_size') else 0.0
    retrieved_data['bid_size'] = float(retrieved_data['bid_size']) if retrieved_data.get('bid_size') else 0.0
    retrieved_data['sequence_id'] = int(retrieved_data['sequence_id']) if retrieved_data.get('sequence_id') else 0

    return jsonify(retrieved_data), 200

@app.route('/retrievehtxbbo/<key>', methods=['GET'])
def retrieve_htxbbo(key):
    """Retrieve data from Redis based on the given key."""
    # Get all fields in the hash
    retrieved_data = r.hgetall(key)
    print(retrieved_data)
    if not retrieved_data:
        return jsonify({"error": "Key not found"}), 404
    retrieved_data['currency'] = str(retrieved_data['currency']) if retrieved_data.get('currency') else "Nan"
    
    # Convert list fields from strings back to lists
    retrieved_data['ask_additional_info'] = retrieved_data['ask_additional_info'].split(',') if retrieved_data.get('ask_additional_info') else []
    retrieved_data['bid_additional_info'] = retrieved_data['bid_additional_info'].split(',') if retrieved_data.get('bid_additional_info') else []

    # Convert numeric fields from strings to their appropriate types
    retrieved_data['ask_size'] = float(retrieved_data['ask_size']) if retrieved_data.get('ask_size') else 0.0
    retrieved_data['bid_size'] = float(retrieved_data['bid_size']) if retrieved_data.get('bid_size') else 0.0
    retrieved_data['sequence_id'] = int(retrieved_data['sequence_id']) if retrieved_data.get('sequence_id') else 0

    return jsonify(retrieved_data), 200
if __name__ == '__main__':
    app.run(debug=True)
