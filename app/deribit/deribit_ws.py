import asyncio
import websockets
import json



msg = \
{
  "jsonrpc" : "2.0",
  "id" : 8691,
  "method" : "public/unsubscribe",
  "params" : {
    "channels" : [
      "BTC_USDC-PERPETUAL"
    ]
  }
}

async def call_api(msg):
   async with websockets.connect('wss://test.deribit.com/ws/api/v2') as websocket:
       await websocket.send(msg)
       while True:
           response = await websocket.recv()
           # do something with the response...
           print(response)

asyncio.get_event_loop().run_until_complete(call_api(json.dumps(msg)))


# class WebSocketFactory:

#     def __init__(self, url):
#         self.url = url
#         self.websocket = None
#         self.loop = asyncio.get_event_loop()

#     async def connect(self):
#         ssl_context = ssl.create_default_context()
#         ssl_context.load_verify_locations(certifi.where())
#         try:
#             self.websocket = await websockets.connect(self.url, ssl=ssl_context)
#             logger.info("WebSocket connection established.")
#             return self.websocket
#         except Exception as e:
#             logger.error(f"Error connecting to WebSocket: {e}")
#             return None

#     async def close(self):
#         if self.websocket:
#             await self.websocket.close()
#             self.websocket = None
