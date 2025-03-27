from app.util import with_db_connection
from pg8000.dbapi import ProgrammingError, DatabaseError
from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS
import traceback

app = Flask(__name__)
CORS(app)


@app.route('/db/get_algo_list', methods=['GET'])
@with_db_connection
def get_algo_list(cursor):
    # user input username and password
    username = request.args.get('username')
    # Execute SELECT query to check for existing users
    try:
        cursor.execute("SELECT jsonb_build_object('username', username,'algo_type', algo_type,'algo_name', algo_name,'lead_exchange',lead_exchange ,'lag_exchange', lag_exchange,'spread',spread ,'qty',qty ,'ccy',ccy,'instrument',instrument,'contract_type',contract_type,'state',state,'updated_at', updated_at) FROM algo_dets WHERE username = %s order by algo_name;", (username,))
        result = cursor.fetchall()
        return jsonify(result)
    except DatabaseError as e:
        print(traceback.format_exc())
    finally:
        cursor.close()  # Close the cursor

@app.route('/db/modify_algo', methods=['POST'])
@with_db_connection
def modify_algo(cursor):
    # Parse JSON data from the request
    data = request.json
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
    instrument = data.get('instrument')
    contract_type = data.get('contract_type')
    print(username,algo_name)
    if not username or not algo_name:
        return jsonify({"error": "Missing required fields"}), 400
    # print(contract_type)
   
    try:
        query = """
        UPDATE algo_dets 
        SET lead_exchange = %s, lag_exchange = %s, spread = %s, qty = %s, ccy = %s, state = %s,instrument=%s,contract_type=%s, updated_at = CURRENT_TIMESTAMP 
        WHERE username = %s AND algo_name = %s
        """
        cursor.execute(query, (lead_exchange, lag_exchange, spread, qty, ccy, state,instrument, contract_type, username, algo_name))
        cursor.connection.commit()  # Commit the transaction
        print('Update success')
        return jsonify({"message": "Status updated successfully"}), 200
    
    except ProgrammingError as e:
        print('error')
        return jsonify({"error": f"Programming error: {e}"}), 500
    except DatabaseError as e:
        print('error')
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        cursor.close()  # Close the cursor

@app.route('/db/add_algo', methods=['POST'])
@with_db_connection
def add_algo(cursor):
    data = request.json
    print(data)
    if not data:
        return jsonify({"error": "Invalid input"}), 400
    # username,algoType, algoName,leadExchange, lagExchange, spread, quantity, ccy,instrument,contractType, state
    username = data.get('username')
    algo_type=data.get('algo_type')
    algo_name = data.get('algo_name')
    lead_exchange = data.get('lead_exchange')
    lag_exchange = data.get('lag_exchange')
    spread = data.get('spread')
    qty = data.get('qty')
    ccy = data.get('ccy')
    instrument = data.get('instrument')
    contract_type = data.get('contract_type')
    state = data.get('state')
    print(username, algo_type,algo_name, lead_exchange, lag_exchange, spread, qty, ccy,instrument,contract_type, state)
    if not username or not algo_name:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        # Execute the INSERT query with RETURNING
        query = """
        INSERT INTO algo_dets (username,algo_type, algo_name, lead_exchange, lag_exchange, spread, qty, ccy,instrument,contract_type, state)
        VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s,%s,%s)
        RETURNING 'Insertion successful' AS status;
        """
        cursor.execute(query, (username, algo_type,algo_name, lead_exchange, lag_exchange, spread, qty, ccy,instrument,contract_type, state))
        result = cursor.fetchone()  # Fetch the returning status message

        cursor.connection.commit()  # Commit the transaction
        return jsonify({"status": result[0]}), 201  # Return the status message in the response


    except Exception as e:
        # Handle any other unexpected errors
        print('error!!')
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()  # Close the cursor

@app.route('/db/delete_algo', methods=['POST'])
@with_db_connection
def delete_algo(cursor):
    data = request.json
    print(data)
    if not data:
        return jsonify({"error": "Invalid input"}), 400
    username = data.get('username')
    algo_name = data.get('algo_name')
    
    if not username or not algo_name:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        # Execute the INSERT query with RETURNING
        query = """
        DELETE FROM algo_dets WHERE username = %s and algo_name =%s
        RETURNING 'Delete successful' AS status;
        """
        cursor.execute(query, (username, algo_name))
        result = cursor.fetchone()  # Fetch the returning status message

        cursor.connection.commit()  # Commit the transaction
        return jsonify({"status": result[0]}), 201  # Return the status message in the response


    except Exception as e:
        # Handle any other unexpected errors
        print('error!!')
        return jsonify({"error": str(e)}), 400
    
    finally:
        cursor.close()  # Close the cursor

if __name__ == "__main__":
    app.run(host= '0.0.0.0',port=5020)