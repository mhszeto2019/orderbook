import asyncio

from okx.websocket.WsPublicAsync import WsPublicAsync
import os
import redis
import configparser
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
# Read the configuration file
config.read(config_file_path)
config_source = 'redis'
REDIS_HOST = config[config_source]['host']
REDIS_PORT = config[config_source]['port']
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

import datetime
import json
def publicCallback(message):
    # print("publicCallback", message)
    # redis_client.hset(redis_key, mapping=message)
    # redis_client.publish(redis_key, json.dumps(message))
    response_data = json.loads(message)
    if 'data' in response_data:
        funding_rate = response_data['data'][0].get('fundingRate', None)
        fundingTime = response_data['data'][0].get('fundingTime', [])
        print('ccy',response_data['data'][0].get('instId',''))
        ccy = response_data['data'][0].get('instId','')
        
        ts = int(response_data['data'][0].get('ts',0))/ 1000
        readable_timestamp = datetime.datetime.fromtimestamp(ts)

        # Format the timestamp as a human-readable string
        formatted_timestamp = readable_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        print(readable_timestamp)
        data_to_client = {"exchange":"OKX","ccy":ccy, "funding_rate": str(round(float(funding_rate) * 100,6))+"% ({})".format(fundingTime),"ts":formatted_timestamp}
        print(data_to_client)
        redis_key = f'okx_fundingrate/{ccy}'
        redis_client.hset(redis_key, mapping=data_to_client)
        redis_client.publish(redis_key, json.dumps(data_to_client))


async def main():
    
    # url = "wss://wspap.okex.com:8443/ws/v5/public?brokerId=9999"
    url = "wss://ws.okx.com:8443/ws/v5/public"
    ws = WsPublicAsync(url=url)
    await ws.start()
    args = []
    arg1 = {"channel": "funding-rate", "instId": "BTC-USD-SWAP"}
    arg2 = {"channel": "instruments", "instType": "SPOT"}
    arg3 = {"channel": "tickers", "instId": "BTC-USDT-SWAP"}
    arg4 = {"channel": "tickers", "instId": "ETH-USDT"}
    args.append(arg1)
    # args.append(arg2)
    # args.append(arg3)
    # args.append(arg4)
    await ws.subscribe(args, publicCallback)
    # await asyncio.sleep(5)
    # print("-----------------------------------------unsubscribe--------------------------------------------")
    # args2 = [arg4]
    # await ws.unsubscribe(args2, publicCallback)
    await asyncio.sleep(60)
    


if __name__ == '__main__':
    asyncio.run(main())
