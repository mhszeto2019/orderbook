import ccxt.pro as ccxtpro
import asyncio
from asyncio import run
from fastapi import FastAPI
app = FastAPI()

async def main():
    exchange = ccxtpro.huobi({'newUpdates': False})
    while True:
        orderbook = await exchange.watchPositions('BTC/USD')
        print(orderbook['asks'][0], orderbook['bids'][0])
    await exchange.close()


asyncio.create_task(main())