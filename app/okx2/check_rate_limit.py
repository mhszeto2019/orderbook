import okx.Account as Trade
import configparser
import os

config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)

config_source = 'okx_live_trade'
apiKey = config[config_source]['apiKey']
secretKey = config[config_source]['secretKey']
passphrase = config[config_source]['passphrase']


# API initialization
apikey = apiKey
secretkey = secretKey
passphrase = passphrase

flag = "0"  # Production trading:0 , demo trading:1

tradeAPI = Trade.TradeAPI(apikey, secretkey, passphrase, False, flag)

# Set leverage for MARGIN instruments under isolated-margin trade mode at pairs level.
result = tradeAPI.account-rate-limit(
    
)
print(result)
