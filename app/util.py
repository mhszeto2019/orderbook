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
# def token_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         # Get the token from the Authorization header
#         token = None
#         if 'Authorization' in request.headers:
#             token = request.headers['Authorization']

#         # If no token is provided
#         if not token:
#             return jsonify({'message': 'Token is missing!'}), 401

#         try:
#             # The token is passed as "Bearer <token>", so split it
#             token = token.split()[1]

#             # Decode the token
#             decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

#             # Add the decoded token to the request context
#             request.user = decoded_token  # You can store the decoded token in request.user

#         except jwt.ExpiredSignatureError:
#             return jsonify({'message': 'Token has expired!'}), 401
#         except jwt.InvalidTokenError:
#             return jsonify({'message': 'Invalid token!'}), 401

#         return f(*args, **kwargs)
#     return decorated_function





import logging
import os
from pathlib import Path

import inspect
# Function to configure and return a logger
def get_logger(log_dir: Path = Path('/var/www/html/orderbook/logs'), log_level: int = logging.DEBUG,logger_name:str = None):
    caller_filename = Path(os.path.basename(__file__)).stem  # This gets the name of the script calling the logger
    # If no logger_name is provided, determine the caller's filename
    if logger_name is None:
        # Inspect the call stack and find the caller's file
        frame = inspect.stack()[1]  # Get the caller's frame
        caller_filename = os.path.splitext(os.path.basename(frame.filename))[0]  # Extract the filename without extension
        logger_name = caller_filename  # Set the logger's name to the caller's filename

    # Ensure the log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    # Define the log file path using the logger name (e.g., main.log)
    log_filename = log_dir / f"{logger_name}.log"

    # Set up the logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Set up file handler
    file_handler = logging.FileHandler(log_filename)
    
    # Add filename to the log format
    # formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(filename)s] - %(message)s')
    formatter = logging.Formatter('%(asctime)s[%(levelname)s]- %(message)s')

    file_handler.setFormatter(formatter)

    # Add handler to the logger if no handlers exist
    if not logger.handlers:
        logger.addHandler(file_handler)

    return logger
# Create and use the logger
logger = get_logger()



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
        # try:
        con = pg8000.connect(
            user=dbusername,         # Change to your PostgreSQL username
            password=dbpassword, # Change to your PostgreSQL password
            host="localhost",         # Host, usually 'localhost' for local connections
            port=5432,                # Default PostgreSQL port
            database=dbname   # Database name
        )

            # Create cursor object to execute queries
            # cursor = con.cursor()

        cursor = conn.cursor()
        try:
            result = func(cursor, conn, *args, **kwargs)
            return result
        finally:
            cursor.close()
            conn.close()

    return wrapper



from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

SECRET_KEY = "your-secret-key"  # Replace with your actual secret

# This defines how FastAPI gets the Authorization header from Swagger and requests
bearer_scheme = HTTPBearer()


def token_required(request: Request):
    token = request.headers.get("Authorization")
    print(token)
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing!")
    
    try:
        # Remove 'Bearer ' from the token string
        token = token.split(" ")[1]
        
        # Decode the token (without verifying the signature for example purposes)
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        # You can store information from the decoded token here for later use (e.g., request.user)
        request.state.user = payload

    except jwt.ExpiredSignatureError:
        # return jsonify({'message': 'Token has expired!'}), 401
        return False
    except jwt.InvalidTokenError:
        # return jsonify({'message': 'Invalid token!'}), 401
        return False


    return True  # The token is valid, so proceed with the route handler

    

