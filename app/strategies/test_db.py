from util import with_db_connection
from pg8000.dbapi import ProgrammingError, DatabaseError
from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
CORS(app)


@app.route('/db/get_algo_list', methods=['GET'])
@with_db_connection
def get_algo_list(cursor):
    # user input username and password
    username = request.form.get('username')
    password = request.form.get('password')
    print(request)
    # Execute SELECT query to check for existing users
    cursor.execute("SELECT jsonb_build_object('username', username,'algo_name', algo_name,'lead_exchange',lead_exchange ,'lag_exchange', lag_exchange,'spread',spread ,'qty',qty ,'ccy',ccy,'state',state,'updated_at', updated_at) FROM algo_dets WHERE username = %s;", ('brennan',))
    result = cursor.fetchall()
    return jsonify(result)


@app.route('/db/modify_status', methods=['POST'])
@with_db_connection
def modify_status(cursor):
    # Parse JSON data from the request
    data = request.json
    print(data)
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    username = data.get('username')
    algo_name = data.get('algo_name')
    lead_exchange = data.get('lead_exchange')
    lag_exchange = data.get('lag_exchange')
    spread = data.get('spread')
    qty = data.get('qty')
    ccy = data.get('ccy')
    state = data.get('state')
    if not username or not algo_name:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        query = """
        UPDATE algo_dets 
        SET lead_exchange = %s, lag_exchange = %s, spread = %s, qty = %s, ccy = %s, state = %s, updated_at = CURRENT_TIMESTAMP 
        WHERE username = %s AND algo_name = %s
        """
        cursor.execute(query, (lead_exchange, lag_exchange, spread, qty, ccy, state, username, algo_name))
        cursor.connection.commit()  # Commit the transaction

        return jsonify({"message": "Status updated successfully"}), 200
    
    except ProgrammingError as e:
        return jsonify({"error": f"Programming error: {e}"}), 500
    except DatabaseError as e:
        return jsonify({"error": f"Database error: {e}"}), 500


# for i in range(100):
#     if i%2 == 0:
#         create_state('username','algo_state',False)
#     else:
#         create_state('username','algo_state',True)


# username, algo_name, lead_exchange, lag_exchange, spread,qty, state
# create_state('username','algo_name','OKX','HTX','200','10',True)

# read_state('username','algo_name')

if __name__ == "__main__":
    app.run(host= '0.0.0.0',port=5020)