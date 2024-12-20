from util import with_db_connection
from pg8000.dbapi import ProgrammingError, DatabaseError
from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
CORS(app)


@app.route('/db/get_state', methods=['GET'])
@with_db_connection
def get_state(cursor):
    # user input username and password
    username = request.form.get('username')
    password = request.form.get('password')

    # Execute SELECT query to check for existing users
    cursor.execute("SELECT * FROM algo_state WHERE username = %s", ('brennan',))
    x = cursor.fetchall()
    print(x)

@app.route('/db/create_state', methods=['GET'])
@with_db_connection
def create_state(cursor, username, algo_name, lead_exchange, lag_exchange, spread, qty, state):
    """Creates a new state record."""
    try:
        query = """
        INSERT INTO algo_state (username, algo_name, lead_exchange, lag_exchange, spread, qty, state)
        VALUES (%s, %s, %s,%s, %s, %s,%s)
        RETURNING username, algo_name, lead_exchange, lag_exchange, spread, state,qty, updated_at;
        """
        cursor.execute(query, (username, algo_name, lead_exchange, lag_exchange, spread, qty, state))
        cursor.connection.commit()  # Commit the transaction
        result = cursor.fetchone()
        print("Record inserted:", result)
    except ProgrammingError as e:
        print(f"Programming error during insert: {e}")
    except DatabaseError as e:
        print(f"Database error during insert: {e}")

@app.route('/db/read_state', methods=['GET'])
@with_db_connection
def read_state(cursor, username, algo_name):
    """Reads the latest state record for the given username and algo_name."""
    try:
        query = """
        SELECT lead_exchange, lag_exchange, spread, state,qty, state, updated_at
        FROM algo_state
        WHERE username = %s AND algo_name = %s
        ORDER BY updated_at DESC
        LIMIT 1;
        """
        # print("Executing query:", query)
        cursor.execute(query, (username, algo_name))
        result = cursor.fetchone()
        if result:
            print("Latest state fetched:", result)
            return result
        else:
            print("No state found for the given criteria.")
            return None
    except ProgrammingError as e:
        print(f"Programming error during read: {e}")
    except DatabaseError as e:
        print(f"Database error during read: {e}")

@with_db_connection
def update_state(cursor, username, algo_name, new_state):
    """Updates an existing state record."""
    try:
        query = """
        UPDATE algo_state
        SET state = %s, updated_at = CURRENT_TIMESTAMP
        WHERE username = %s AND algo_name = %s
        RETURNING username, algo_name, state, updated_at;
        """
        # print("Executing query:", query)
        cursor.execute(query, (new_state, username, algo_name))
        cursor.connection.commit()  # Commit the transaction
        result = cursor.fetchone()
        if result:
            print("Record updated:", result)
            return result
        else:
            print("No record found to update.")
            return None
    except ProgrammingError as e:
        print(f"Programming error during update: {e}")
    except DatabaseError as e:
        print(f"Database error during update: {e}")

@with_db_connection
def delete_state(cursor, username, algo_name):
    """Deletes a state record."""
    try:
        query = """
        DELETE FROM algo_state
        WHERE username = %s AND algo_name = %s
        RETURNING username, algo_name;
        """
        # print("Executing query:", query)
        cursor.execute(query, (username, algo_name))
        cursor.connection.commit()  # Commit the transaction
        result = cursor.fetchone()
        if result:
            print("Record deleted:", result)
            return result
        else:
            print("No record found to delete.")
            return None
    except ProgrammingError as e:
        print(f"Programming error during delete: {e}")
    except DatabaseError as e:
        print(f"Database error during delete: {e}")


# for i in range(100):
#     if i%2 == 0:
#         create_state('username','algo_state',False)
#     else:
#         create_state('username','algo_state',True)


# username, algo_name, lead_exchange, lag_exchange, spread,qty, state
# create_state('username','algo_name','OKX','HTX','200','10',True)

read_state('username','algo_name')