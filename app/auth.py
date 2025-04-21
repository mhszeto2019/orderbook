from flask import Flask, jsonify, request, Blueprint
from flask_cors import CORS 
import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
import os
import configparser
from app.util import token_required
from app.util import get_logger 
logger = get_logger()

config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', 'config_folder', 'credentials.ini')
print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)
app = Flask(__name__)
CORS(app)

config_source = config['dbchoice']['db']
dbusername = config[config_source]['username']
dbpassword = config[config_source]['password']
dbname = config[config_source]['dbname']
from cryptography.fernet import Fernet

import pg8000

# Example: A simple in-memory database for users
users = {}

# Create a blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# config_source = 'secret'
SECRET_KEY = config['jwt_secret']['secret_key']
# Secret key for JWT encoding/decoding

app = Flask(__name__)

# Register the blueprint with a specific URL prefix
app.register_blueprint(auth_bp, url_prefix='/auth')

# Enable CORS for all origins (adjust as necessary for your use case)
CORS(app)
import redis
import json
redis_host = 'localhost'
redis_port = 6379
redis_db = 0  # Default database
r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
username = None
ip_address = None

def with_db_connection(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Establish PostgreSQL connection
        try:
            con = pg8000.connect(
                user=dbusername,         # Change to your PostgreSQL username
                password=dbpassword, # Change to your PostgreSQL password
                host="localhost",         # Host, usually 'localhost' for local connections
                port=5432,                # Default PostgreSQL port
                database=dbname   # Database name
            )

            # Create cursor object to execute queries
            cursor = con.cursor()

            # Pass the connection and cursor to the wrapped function
            result = func(cursor, *args, **kwargs)

        finally:
            # Always ensure the cursor and connection are closed
            cursor.close()
            con.close()

        return result
    return wrapper


## Register route using the decorator
@app.route('/register', methods=['POST'])
@with_db_connection
def register(cursor):
    # user input username and password
    username = request.form.get('username')
    password = request.form.get('password')

    # Execute SELECT query to check for existing users
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    # cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    # If a user already exists, return an error
    if rows:
        return jsonify({"message": "User already exists!"}), 400

    # Hash the password,secreket,apikey and passphrase using bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    # hashed_secretkey = bcrypt.hashpw(secretkey.encode('utf-8'), bcrypt.gensalt())
    # hashed_apikey = bcrypt.hashpw(apikey.encode('utf-8'), bcrypt.gensalt())
    # hashed_passphrase = bcrypt.hashpw(passphrase.encode('utf-8'), bcrypt.gensalt())

    # Insert new user into the database
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
    
    # Commit the transaction to save the data
    cursor.connection.commit()

    ip_address = request.remote_addr if request else 'Unknown'
    logger.info("User:{} registration successful. - IP:{}".format(username,ip_address))
    return jsonify({"message": "Registration successful!"}), 201


# Login route
@app.route('/login', methods=['POST'])
@with_db_connection
def login(cursor):
    global username,ip_address
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Check if the user exists
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    userrow = cursor.fetchone()
    if not userrow:
        return jsonify({"message": "User not found!!"}), 404
    # Check if the password matches
    username,hashed_pw = userrow
    if not bcrypt.checkpw(password.encode('utf-8'), bytes.fromhex(hashed_pw[2:])):
        return jsonify({"message": "Invalid password!"}), 401
    try:
        cursor.execute("""
        SELECT 
            u.username, 
            u.password, 
            COALESCE(
                JSONB_OBJECT_AGG(ac.exchange, 
                    JSONB_BUILD_OBJECT(
                        'apikey', COALESCE(ac.apikey, 'N/A'),
                        'secretkey', COALESCE(ac.secretkey, 'N/A'),
                        'passphrase', COALESCE(ac.passphrase, 'N/A')
                    )
                ),
                '{}'::jsonb
            ) AS api_credentials
        FROM 
            users u
        LEFT JOIN 
            api_credentials ac ON u.username = ac.username
        WHERE 
            u.username = %s
        GROUP BY 
            u.username, u.password; 
            """, (username,))
        # cursor.execute("SELECT * FROM users")
        row = cursor.fetchone()
        # If a user doesnt exist, return an error
        
        username,hashed_pw,api_creds_dict = row



        # Generate or retrieve a key for encryption (do this once, then store the key securely)
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        # Encrypt the sensitive data
        if api_creds_dict:
            encrypted_data = cipher_suite.encrypt(json.dumps({
                'htx_secretkey': api_creds_dict['htx']['secretkey'],
                'htx_apikey': api_creds_dict['htx']['apikey'],
                'okx_secretkey': api_creds_dict['okx']['secretkey'],
                'okx_apikey': api_creds_dict['okx']['apikey'],
                'okx_passphrase': api_creds_dict['okx']['passphrase']
            }).encode())

        # Store the encrypted data in Redis using a user-specific key
        cache_key = f"user:{username}:api_credentials"
        r.set(cache_key, encrypted_data)

        # Create JWT token
        payload = {
            'sub': username,  # Subject (user identifier)
            'iat': datetime.utcnow(),  # Issued at time
            'exp': datetime.utcnow() + timedelta(hours=1000)  # Expiration time (1 hour)
        }

        # Encode the JWT token using the SECRET_KEY and HS256 algorithm
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        ip_address = request.remote_addr if request else 'Unknown'
        print("User:{} login successful. - IP:{}".format(username,ip_address))
        logger.info("User:{} login successful. - IP:{}".format(username,ip_address))
        return jsonify({
            'message': 'Login Successful!',
            'token': token,  # Send the token as the response
            'key':str(key),
            'username':username
            # 'secretkey':hashed_secretkey,
            # 'apikey':hashed_apikey,
            # 'passphrase':hashed_passphrase
        })

    except Exception as e:
        print(e,type(e))
        print("error retrieving api credentials")
        error_msg = e.args[0].get('M', 'Unknown error')
        return jsonify({
            'message':  "Db error:{} (possibly no secretkey)".format(error_msg)
        }), 402

# Login route
@app.route('/logout', methods=['GET'])
def logout():
    global username, ip_address
    print("User:{} logout successful. - IP:{}".format(username,ip_address))
    # okx_secretkey_apikey_passphrase = r.get('okx_secretkey_apikey_passphrase')
    # Retrieve the encryption key from a secure location (e.g., environment variable, secrets manager)
    # key =  # This key should be securely stored and shared between apps
    cache_key = f"user:{username}:api_credentials"
    r.delete(cache_key)
    
    logger.info("User:{} logout successful. - IP:{}".format(username,ip_address))
    return jsonify({'message':'Logout successful'})


@app.route('/test', methods=['POST'])
@token_required
@with_db_connection
def test(cursor):
    global username
    print('JWT verified. This is a secured route.')
    ip_address = request.remote_addr if request else 'Unknown'
    logger = get_logger('app')
    logger.info("User:{} login successful. - IP:{}".format(username,ip_address))
    # Your logic for the secured endpoint
    return jsonify({"message": "Access granted to the secured endpoint!"})


if __name__ == '__main__':
    app.run(debug=True)