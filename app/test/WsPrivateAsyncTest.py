import asyncio

from okx.websocket.WsPrivateAsync import WsPrivateAsync

def privateCallback(message):
    print("privateCallback", message)
import os

import json
import configparser
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)

config_source = 'okx_live_trade'

apiKey = config[config_source]['apiKey']
secretKey = config[config_source]['secretKey']
passphrase = config[config_source]['passphrase']

async def main():
    # url = "wss://wspap.okx.com:8443/ws/v5/private"
    url = "wss://ws.okx.com:8443/ws/v5/private"
    ws = WsPrivateAsync(
            # apiKey="cfa32491-8e93-4537-9106-e2a36305a936",
            # passphrase="Trade@1998",
            # secretKey="434E8A9CC1A729DB292C0819AAE8FBAF",
            apiKey = apiKey,
            passphrase=passphrase,
            secretKey=secretKey,
            url=url,
            useServerTime=False
    )
    await ws.start()
    args = []
    arg1 = {"channel": "account", "ccy": "BTC"}
    arg2 = {"channel": "orders", "instType": "ANY"}
    arg3 = {"channel": "balance_and_position"}
    args.append(arg1)
    args.append(arg2)
    args.append(arg3)
    await ws.subscribe(args, callback=privateCallback)
    await asyncio.sleep(30)
    print("-----------------------------------------unsubscribe--------------------------------------------")
    args2 = [arg2]
    await ws.unsubscribe(args2, callback=privateCallback)
    await asyncio.sleep(30)
    print("-----------------------------------------unsubscribe all--------------------------------------------")
    args3 = [arg1, arg3]
    await ws.unsubscribe(args, callback=privateCallback)


if __name__ == '__main__':
    asyncio.run(main())
