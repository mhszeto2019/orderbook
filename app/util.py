import gzip
import json
import datetime

from functools import wraps
from flask import request, jsonify
import jwt

import logging
import os
from datetime import datetime

import configparser
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', 'config_folder', 'credentials.ini')
print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)

config_source = 'jwt_secret'

SECRET_KEY = config[config_source]['secret_key']

def decoder(binary_code):
    uncoded_msg = gzip.decompress(binary_code).decode("utf-8")
    json_uncoded = json.loads(uncoded_msg)
    return json_uncoded


def unix_ts_to_datetime(unix_ts):
    if isinstance(unix_ts, str):
        unix_ts = int(unix_ts)
    # Check if the timestamp is in milliseconds and convert if necessary
    if len(str(unix_ts)) > 10:  # Assuming timestamps longer than 10 digits are in milliseconds
        unix_ts /= 1000
    # Convert the timestamp to a datetime string
    ts = datetime.datetime.fromtimestamp(unix_ts).strftime('%Y-%m-%d%H:%M:%S')
    # print(ts)  # This will print the converted date and time
    return ts

def standardised_ccy_naming(ccy):
    
    ccy = ccy.lower()
    ccy = ccy.replace('-','')
    ccy = ccy.replace('_','')
    # print("Convert {} to {}".format(ccy,ccy))
    return ccy
    
def mapping_for_ccy(standardised_ccy):
    if standardised_ccy in {"btc_cw","btcusdswap"}:
        return str("btc_coinmargin")
    else:
        return standardised_ccy
    
def format_arr_4dp(arr):
    formatted_arr = [
    [f"{float(ele[0]):.4f}", f"{float(ele[1]):.4f}"]  # Format both price and quantity
    for ele in arr
]
    return formatted_arr

def format_arr_1dp(arr):
    formatted_arr = [
    [f"{float(ele[0]):.1f}", f"{float(ele[1]):.1f}"]  # Format both price and quantity
    for ele in arr
]
    return formatted_arr


# Decorator for checking JWT token
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the token from the Authorization header
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']

        # If no token is provided
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # The token is passed as "Bearer <token>", so split it
            token = token.split()[1]

            # Decode the token
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

            # Add the decoded token to the request context
            request.user = decoded_token  # You can store the decoded token in request.user

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401

        return f(*args, **kwargs)
    return decorated_function

import logging
import os

# Define the central log directory for all applications
LOG_DIR = '/var/www/html/orderbook/logs'

# Ensure the log directory exists (create it once for all apps)
os.makedirs(LOG_DIR, exist_ok=True)

def get_logger(app_name):
    """
    Sets up and returns a logger for a specific application with additional details like IP address.
    
    Args:
    - app_name (str): The name of the application (used for log filename).
    
    Returns:
    - logger (logging.Logger): Configured logger instance.
    """
    # Log filename specific to the application
    log_filename = os.path.join(LOG_DIR, f'orderbook_{app_name}.log')
    
    # Create a logger specific to the application
    logger = logging.getLogger(app_name)
    
    # Check if the logger has handlers already to avoid duplicates
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)  # Set the logging level
        
        # Create a file handler, which will create the log file if it doesn't exist
        file_handler = logging.FileHandler(log_filename, mode='a')
        file_handler.setLevel(logging.INFO)
        
        # Define the logging format, including timestamp and IP address (dynamically obtained)
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        # Try to get the client's IP address from the request
        ip_address = request.remote_addr if request else 'Unknown'
        
        log_format = f'{log_format}'
        
        formatter = logging.Formatter(log_format)
        file_handler.setFormatter(formatter)
        
        # Attach the file handler to the logger
        logger.addHandler(file_handler)
    
    return logger

# config_source = 'localdb'
config_source = config['dbchoice']['db']
dbusername = config[config_source]['username']
dbpassword = config[config_source]['password']
dbname = config[config_source]['dbname']

import pg8000

# db connecter wrapper for function 
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

