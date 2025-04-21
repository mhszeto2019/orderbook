# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

# Set environment variables for your credentials
# Read more at http://twil.io/secure
import os
import sys
sys.path.insert(0, "/home/brenn/environments/test/lib/python3.10/site-packages")
from twilio.rest import Client
import time
from twilio.twiml.voice_response import VoiceResponse
import asyncio
import threading
# Run the alert function
from datetime import datetime
import time
import pg8000
from pg8000.dbapi import ProgrammingError, DatabaseError
from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS
import traceback
import configparser
from app.htx2.HtxOrderClass import HuobiCoinFutureRestTradeAPI
from okx import Account


config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '../..','config_folder', 'credentials.ini')
print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)

config_source = config['dbchoice']['db']
dbusername = config[config_source]['username']
dbpassword = config[config_source]['password']
dbname = config[config_source]['dbname']

# Twilio API Credentials (Replace with yours)
ACCOUNT_SID = config['twilio']['account_sid']
AUTH_TOKEN = config['twilio']['auth_token']
TWILIO_PHONE = config['twilio']['phone_number']

account_sid = ACCOUNT_SID
auth_token = AUTH_TOKEN
client = Client(account_sid, auth_token)

call = client.calls.create(
  url="http://demo.twilio.com/docs/voice.xml",
  to="+6586134493",
  from_="+17123838179"
)

print(call.sid)

