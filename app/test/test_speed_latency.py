import aiohttp
import asyncio
import time

async def fetch():
    url = "https://api.huobi.pro/market/depth?symbol=btcusdt&depth=5&type=step0"
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        async with session.get(url) as response:
            data = await response.json()
            print(f"Request Time: {time.time() - start_time} seconds")
            print(data)

loop = asyncio.get_event_loop()
loop.run_until_complete(fetch())
