"""
Description:
    Deribit WebSocket Asyncio Example.

    - Authenticated connection.

Usage:
    python3.9 dbt-ws-authenticated-example.py

Requirements:
    - websocket-client >= 1.2.1
"""

# built ins
import asyncio
import sys
import json
from typing import Dict
from datetime import datetime, timedelta

# installed
import websockets
import shutil
import logging
from pathlib import Path

from datetime import datetime, timedelta

import os
import configparser
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
# print("Config file path:", config_file_path)
# Read the configuration file
config.read(config_file_path)
config_source = 'deribit'
client_id = config[config_source]['apikey']
client_secret = config[config_source]['secretkey']

from app.deribit.credentials import client_id, client_secret, client_url


# Define the log directory and the log file name
LOG_DIR = Path('/var/www/html/orderbook/logs')
log_filename = LOG_DIR / (Path(__file__).stem + '.log')

# === Step 1: Archive previous day's log if exists ===
if log_filename.exists():
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    archive_dir = LOG_DIR / yesterday
    archive_dir.mkdir(parents=True, exist_ok=True)
    archived_log_path = archive_dir / log_filename.name
    shutil.move(str(log_filename), str(archived_log_path))

# === Step 2: Ensure log directory exists ===
LOG_DIR.mkdir(parents=True, exist_ok=True)

# === Step 3: Set up logging ===
file_handler = logging.FileHandler(log_filename)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)

logger = logging.getLogger('Deribit_auth')
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)


class main:
    def __init__(
        self,
        ws_connection_url: str,
        client_id: str,
        client_secret: str,
        instrument_name: str
            ) -> None:
        # Async Event Loop
        self.loop = asyncio.get_event_loop()

        # Instance Variables
        self.ws_connection_url: str = ws_connection_url
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.websocket_client: websockets.WebSocketClientProtocol = None
        self.refresh_token: str = None
        self.refresh_token_expiry_time: int = None
        self.instrument_name: str = instrument_name
        # Start Primary Coroutine
        self.loop.run_until_complete(
            self.ws_manager()
            )

    async def ws_manager(self) -> None:
        async with websockets.connect(
            self.ws_connection_url,
            ping_interval=None,
            compression=None,
            close_timeout=60
            ) as self.websocket_client:

            # Authenticate WebSocket Connection
            await self.ws_auth()

            # Establish Heartbeat
            await self.establish_heartbeat()

            # Start Authentication Refresh Task
            self.loop.create_task(
                self.ws_refresh_auth()
                )

            # Subscribe to the specified WebSocket Channel
            self.loop.create_task(
                self.ws_operation(
                    operation='subscribe',
                    # raw means no aggregation applied
                    ws_channel=f'trades.{self.instrument_name}.raw'
                    )
                )

            while True:
                message: bytes = await self.websocket_client.recv()
                message: Dict = json.loads(message)
                # logging.info(message)
                logger.info(message)
                print(message)

                if 'id' in list(message):
                    if message['id'] == 9929:
                        if self.refresh_token is None:
                            logger.info('Successfully authenticated WebSocket Connection')
                        else:
                            logger.info('Successfully refreshed the authentication of the WebSocket Connection')

                        self.refresh_token = message['result']['refresh_token']

                        # Refresh Authentication well before the required datetime
                        if message['testnet']:
                            expires_in: int = 300
                        else:
                            expires_in: int = message['result']['expires_in'] - 240

                        self.refresh_token_expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)

                    elif message['id'] == 8212:
                        # Avoid logger Heartbeat messages
                        continue

                elif 'method' in list(message):
                    # Respond to Heartbeat Message
                    if message['method'] == 'heartbeat':
                        await self.heartbeat_response()

            else:
                logger.info('WebSocket connection has broken.')
                sys.exit(1)

    async def establish_heartbeat(self) -> None:
        """
        Requests DBT's `public/set_heartbeat` to
        establish a heartbeat connection.
        """
        msg: Dict = {
                    "jsonrpc": "2.0",
                    "id": 9098,
                    "method": "public/set_heartbeat",
                    "params": {
                              "interval": 10
                               }
                    }

        await self.websocket_client.send(
            json.dumps(
                msg
                )
                )

    async def heartbeat_response(self) -> None:
        """
        Sends the required WebSocket response to
        the Deribit API Heartbeat message.
        """
        msg: Dict = {
                    "jsonrpc": "2.0",
                    "id": 8212,
                    "method": "public/test",
                    "params": {}
                    }

        await self.websocket_client.send(
            json.dumps(
                msg
                )
                )

    async def ws_auth(self) -> None:
        """
        Requests DBT's `public/auth` to
        authenticate the WebSocket Connection.
        """
        msg: Dict = {
                    "jsonrpc": "2.0",
                    "id": 9929,
                    "method": "public/auth",
                    "params": {
                              "grant_type": "client_credentials",
                              "client_id": self.client_id,
                              "client_secret": self.client_secret
                               }
                    }

        await self.websocket_client.send(
            json.dumps(
                msg
                )
            )

    async def ws_refresh_auth(self) -> None:
        """
        Requests DBT's `public/auth` to refresh
        the WebSocket Connection's authentication.
        """
        while True:
            if self.refresh_token_expiry_time is not None:
                if datetime.utcnow() > self.refresh_token_expiry_time:
                    msg: Dict = {
                                "jsonrpc": "2.0",
                                "id": 9929,
                                "method": "public/auth",
                                "params": {
                                          "grant_type": "refresh_token",
                                          "refresh_token": self.refresh_token
                                            }
                                }

                    await self.websocket_client.send(
                        json.dumps(
                            msg
                            )
                            )

            await asyncio.sleep(150)

    async def ws_operation(
        self,
        operation: str,
        ws_channel: str
            ) -> None:
        """
        Requests `public/subscribe` or `public/unsubscribe`
        to DBT's API for the specific WebSocket Channel.
        """
        await asyncio.sleep(5)

        msg: Dict = {
                    "jsonrpc": "2.0",
                    "method": f"public/{operation}",
                    "id": 42,
                    "params": {
                        "channels": [ws_channel]
                        }
                    }

        await self.websocket_client.send(
            json.dumps(
                msg
                )
            )


if __name__ == "__main__":
    # logger
    # DBT LIVE WebSocket Connection URL
    ws_connection_url: str = 'wss://www.deribit.com/ws/api/v2'
    # DBT TEST WebSocket Connection URL
    # ws_connection_url: str = 'wss://test.deribit.com/ws/api/v2'

    # DBT Client ID
    client_id: str = client_id
    # DBT Client Secret
    client_secret: str = client_secret

    client = main(
         ws_connection_url=ws_connection_url,
         client_id=client_id,
         client_secret=client_secret,
         instrument_name= "BTC-PERPETUAL"
        
         )