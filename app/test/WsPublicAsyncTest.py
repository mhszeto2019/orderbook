import asyncio

from okx.websocket.WsPublicAsync import WsPublicAsync

def publicCallback(message):
    print("publicCallback", message)


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
    # args.append(arg1)
    # args.append(arg2)
    args.append(arg3)
    # args.append(arg4)
    await ws.subscribe(args, publicCallback)
    # await asyncio.sleep(5)
    print("-----------------------------------------unsubscribe--------------------------------------------")
    # args2 = [arg4]
    await ws.unsubscribe(args, publicCallback)
    await asyncio.sleep(15)
    print("-----------------------------------------subscribe again--------------------------------------------")

    await ws.subscribe(args, publicCallback)

    await asyncio.sleep(15)
    # print("-----------------------------------------unsubscribe all--------------------------------------------")
    # args3 = [arg1, arg2, arg3]
    # await ws.unsubscribe(args3, publicCallback)
    # await ws.unsubscribe(args, publicCallback)


if __name__ == '__main__':
    asyncio.run(main())
