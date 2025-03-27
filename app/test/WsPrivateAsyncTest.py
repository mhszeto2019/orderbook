import asyncio

from okx.websocket.WsPrivateAsync import WsPrivateAsync

def privateCallback(message):
    print("privateCallback", message)

import os
import random 
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

print(apiKey,secretKey,passphrase)
async def main():
    # url = "wss://ws.okx.com:8443/ws/v5/private"
    url = "wss://ws.okx.com:8443/ws/v5/private"
    ws = WsPrivateAsync(
            apiKey = apiKey,
            passphrase=passphrase,
            secretKey=secretKey,
            url=url,
            useServerTime=False
    )
    await ws.start()

    args = []

    """Continuously subscribe to a random currency"""
    currencies = ["BTC", "ETH", "LTC", "XRP", "ADA"]  # Add more as needed


# Example usage
# asyncio.run(subscribe_random_currency(ws, privateCallback))
    while True:
        random_ccy = random.choice(currencies)
        arg1 = {"channel": "account", "ccy": random_ccy}
        # arg2 = {"channel": "orders", "instType": "ANY"}
        # arg3 = {"channel": "balance_and_position"}
        args.append(arg1)
        # args.append(arg2)
        # args.append(arg3)
        await ws.subscribe(args, callback=privateCallback)
        await asyncio.sleep(30)
        args.remove(arg1)
        print(args)

        await ws.unsubscribe(args,callback=privateCallback)
        arg1 = {"channel": "account", "ccy": random_ccy}
        args.append(arg1)
        print(args)
        await ws.subscribe(args, callback=privateCallback)

    # print("-----------------------------------------unsubscribe--------------------------------------------")
    # args2 = [arg2]
    # await ws.unsubscribe(args2, callback=privateCallback)
    # await asyncio.sleep(30)
    # print("-----------------------------------------unsubscribe all--------------------------------------------")
    # args3 = [arg1, arg3]
    # await ws.unsubscribe(args, callback=privateCallback)


if __name__ == '__main__':
    asyncio.run(main())
