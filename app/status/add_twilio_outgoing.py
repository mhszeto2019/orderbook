# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client
import configparser


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

NUMBER_TO_ADD = "+6597320731"


# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid =ACCOUNT_SID
auth_token = AUTH_TOKEN
client = Client(account_sid, auth_token)

# GETTING VERIFIED NUMBERS
outgoing_caller_ids = client.outgoing_caller_ids.list(limit=20)
for record in outgoing_caller_ids:
    print(record.sid)
    outgoing_caller_id = client.outgoing_caller_ids(
        record.sid
    ).fetch()
    print(outgoing_caller_id.friendly_name)

# VERIFYING NUMBER
# validation_request = client.validation_requests.create(
#     friendly_name="Trader Seto's number",
#     phone_number="+6597320731",
#     status_callback="https://somefunction.twil.io/caller-id-validation-callback",
# )
# print(validation_request.account_sid)