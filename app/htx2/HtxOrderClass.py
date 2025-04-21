# -*- coding:utf-8 -*-
import gzip
import json
import copy
import hmac
import base64
import urllib
import hashlib
import datetime
import time
from urllib.parse import urljoin
import sys
import os
import traceback
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append('/var/www/html/orderbook/app/htx2')
import aiohttp
import requests

from pathlib import Path
# Logger 
# Define the log directory and the log file name
LOG_DIR = Path('/var/www/html/orderbook/logs')
log_filename = LOG_DIR / (Path(__file__).stem + '.log')
os.makedirs(LOG_DIR, exist_ok=True)
# Set up basic logging configuration
import logging
file_handler = logging.FileHandler(log_filename)
# Set up a basic formatter

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger = logging.getLogger('htxorderclass')
logger.setLevel(logging.DEBUG)  # Set log level
# Add the file handler to the logger
logger.addHandler(file_handler)


from alpha.utils.request import AsyncHttpRequests
from alpha.const import USER_AGENT
import asyncio

__all__ = ("HuobiCoinFutureRestTradeAPI",)


class HuobiCoinFutureRestTradeAPI:
    """ Huobi USDT Swap REST API Client.

    Attributes:
        host: HTTP request host.
        access_key: Account's ACCESS KEY.
        secret_key: Account's SECRET KEY.
        passphrase: API KEY Passphrase.
    """

    def __init__(self, host, access_key, secret_key):
        """ initialize REST API client. """
        self._host = host
        self._access_key = access_key
        self._secret_key = secret_key

    async def get_positions(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
        try:
            """ Get open order information.

            Args:
                symbol: Currency name, e.g. BTC.
                index: Page index, default 1st page.
                size: Page size, Default 20，no more than 50.

            Returns:
                success: Success results, otherwise it's None.
                error: Error information, otherwise it's None.
            """
            uri = "/swap-api/v1/swap_position_info"

            json_dict = await self.request("POST", uri, body=body, auth=True)
            # print("JSON DICT",json_dict)

            return json_dict
        except Exception as e:
            logger.error(f"Exception in get_positions:{traceback.format_exc()}")
    
    async def get_cross_positions(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
        try:
            """ Get open order information.

            Args:
                symbol: Currency name, e.g. BTC.
                index: Page index, default 1st page.
                size: Page size, Default 20，no more than 50.

            Returns:
                success: Success results, otherwise it's None.
                error: Error information, otherwise it's None.
            """
            uri = "/swap-api/v1/swap_cross_position_info"

            json_dict = await self.request("POST", uri, body=body, auth=True)

            return json_dict
        except Exception as e:
            logger.error(f"Exception in get_cross_positions:{traceback.format_exc()}")

    async def create_swap_orders(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
     
        json_response2 = {}

        try: 
            body = {"orders_data":body}
            logger.debug(body)
            # logger.debug(body)
            uri = "/swap-api/v1/swap_batchorder"
            # success, error = await self.request("POST", uri, body=body, auth=True)
            json_dict = await self.request("POST", uri, body=body, auth=True)

            if json_dict['data']['errors']:
                logger.debug(f"ERRORS IN JSON DICT{json_dict}")
                json_response2['data'] = [json_dict['data']]
            else:
                # json_response2 = self.format_message(json_dict)
                json_response2['data'] = [{"ordId":json_dict['data']['success'][0]['order_id'],"sCode":json_dict['sCode'],"ts":json_dict['ts'],"exchange":"htx"}]
                json_response2['rate_limit_remaining'] = json_dict['rate_limit_remaining']

        except Exception as e:
            logger.error(f"Error in create_swap_order: {traceback.format_exc()}")
            raise Exception

        return json_response2
    
    async def place_order(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
        try:
            """ Get open order information.
            Args:
                symbol: Currency name, e.g. BTC.
                index: Page index, default 1st page.
                size: Page size, Default 20，no more than 50.

            Returns:
                success: Success results, otherwise it's None.
                error: Error information, otherwise it's None.
            """
            uri = "/swap-api/v1/swap_order"
            
            json_dict = await self.request("POST", uri, body=body, auth=True)

            json_response2 = self.format_message(json_dict)
        
            return json_response2
            
        except Exception as e:
            logger.error(f"Exception in place_order:{traceback.format_exc()}")


    
    async def get_contract_positions(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
        try:
            """ Get open order information.

            Args:
                symbol: Currency name, e.g. BTC.
                index: Page index, default 1st page.
                size: Page size, Default 20，no more than 50.

            Returns:
                success: Success results, otherwise it's None.
                error: Error information, otherwise it's None.
            """
            uri = "/api/v1/contract_position_info"

            json_dict = await self.request("POST", uri, body=body, auth=True)
            # print("JSON DICT",json_dict)

            return json_dict
        except Exception as e:
            logger.error(f"Exception in place_contract_position:{traceback.format_exc()}")

    async def place_contract_order(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
        try:
            """ Get open order information.

            Args:
                symbol: Currency name, e.g. BTC.
                index: Page index, default 1st page.
                size: Page size, Default 20，no more than 50.

            Returns:
                success: Success results, otherwise it's None.
                error: Error information, otherwise it's None.
            """
            uri = "/api/v1/contract_order"
            json_dict = await self.request("POST", uri, body=body, auth=True)
            json_response2 = self.format_message(json_dict)
        
            return json_response2
        except Exception as e:
            logger.error(f"Exception in place_contract_order:{traceback.format_exc()}")


    async def swap_cancel_after(self, on_off, time_out=5000):

        uri = "/swap-api/v1/swap-cancel-after"
        body = {
            "on_off": on_off
        }

        if time_out:
            body.update({"time_out": time_out})

        json_dict = await self.request("POST", uri, body=body, auth=True)
        logger.debug(f"JSON DICT IN CANCEL AFTER{json_dict}")
        return json_dict

    async def revoke_order_all(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
        try:
            """ Revoke all orders.

            Args:
                contract_code: such as "BTC-USD".

            Returns:
                success: Success results, otherwise it's None.
                error: Error information, otherwise it's None.

            * NOTE: 1. If input `contract_code`, only matching this contract code.
                    2. If not input `contract_code`, matching by `symbol + contract_type`.
            """
            uri = "/swap-api/v1/swap_cancelall"
            

            json_dict = await self.request("POST", uri, body=body, auth=True)
            return json_dict
            
        except Exception as e:
            logger.error(f"Error in ggetet_tpsl_info: {traceback.format_exc()}")


    async def revoke_order(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
        try:
            """ Revoke an order.

            Args:
                contract_code: such as "BTC-USD".
                order_id: Order ID.

            Returns:
                success: Success results, otherwise it's None.
                error: Error information, otherwise it's None.
            """
            uri = "/swap-api/v1/swap_cancel"
         
            json_dict = await self.request("POST", uri, body=body, auth=True)
            if json_dict:
                logger.debug(json_dict)
            return json_dict

        except Exception as e:
            logger.error(f"Error in revoke_order: {traceback.format_exc()}")

    async def get_open_orders(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
        try:
            # Args:
            #     contract_code: such as "BTC-USD".
            #     index: Page index, default 1st page.
            #     size: Page size, Default 20，no more than 50.

            # Returns:
            #     success: Success results, otherwise it's None.
            #     error: Error information, otherwise it's None.
            uri = "/swap-api/v1/swap_openorders"
        
            json_dict = await self.request("POST", uri, body=body, auth=True)
            return json_dict

        except Exception as e:
            logger.error(f"Error in get_open_orders: {traceback.format_exc()}")


    async def get_order_info(self,  symbol,body, order_ids=None, client_order_ids=None):
        try:
            """ Get order information.

            Args:
                contract_code: such as "BTC-USD".
                order_ids: Order ID list. (different IDs are separated by ",", maximum 20 orders can be requested at one time.)
                client_order_ids: Client Order ID list. (different IDs are separated by ",", maximum 20 orders can be requested at one time.)

            Returns:
                success: Success results, otherwise it's None.
                error: Error information, otherwise it's None.
            """
            uri = "/swap-api/v1/swap_order_info"
            

            json_dict = await self.request("POST", uri, body=body, auth=True)

            return json_dict
        except Exception as e:
            logger.error(f"Error in get_order_info: {traceback.format_exc()}")

    async def get_tpsl_info(self,  symbol,body, order_id=None, client_order_id=None):
        try:
            """ Get order information.

            Args:
                contract_code: such as "BTC-USD".
                order_ids: Order ID list. (different IDs are separated by ",", maximum 20 orders can be requested at one time.)
                client_order_ids: Client Order ID list. (different IDs are separated by ",", maximum 20 orders can be requested at one time.)

            Returns:
                success: Success results, otherwise it's None.
                error: Error information, otherwise it's None.
            """
            uri = "/swap-api/v1/swap_relation_tpsl_order"
            

            json_dict = await self.request("POST", uri, body=body, auth=True)
            return json_dict
        except Exception as e:
            logger.error(f"Error in get_tpsl_info: {traceback.format_exc()}")
            
    
    async def get_funding_rate(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
        try: 
            uri = "/swap-api/v1/swap_funding_rate"
        
            json_dict = await self.request("GET", uri, body,  auth=True)
            return json_dict
        except Exception as e:
            logger.error(f"Error in get_funding_rate: {traceback.format_exc()}")

    async def request(self, method, uri, params=None, body=None, headers=None, auth=False):
        """ Do HTTP request.
        
        Args:
            method: HTTP request method. `GET` / `POST` / `DELETE` / `PUT`.
            uri: HTTP request uri.
            params: HTTP query params.
            body: HTTP request body.
            headers: HTTP request headers.
            auth: If this request requires authentication.

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        current_time = time.time()

        if uri.startswith("http://") or uri.startswith("https://"):
            url = uri
        else:
            
            url = self._host + uri
        if auth:
            timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            
            # Encode the timestamp with URI encoding in uppercase
            # encoded_timestamp = urllib.parse.quote(timestamp, safe='')
            logger.debug(f"UTC TIMESTAMP:{timestamp}")
            # print(timestamp,encoded_timestamp)
            params = params if params else {}
            params.update({"AccessKeyId": self._access_key,
                           "SignatureMethod": "HmacSHA256",
                           "SignatureVersion": "2",
                           "Timestamp": timestamp})
            
            params["Signature"] = self.generate_signature(method, params, uri)

        if not headers:
            headers = {}
        if method == "GET":
            headers["Content-type"] = "application/x-www-form-urlencoded"
            headers["User-Agent"] = USER_AGENT
            # _, success, error = await AsyncHttpRequests.fetch("GET", url, params=params, headers=headers, timeout=10)
            try:
                
                # response_dict =await self.aiohttp_request("GET", url, params=params, data=body, headers=headers)
                response_dict = self.python_request("GET", url, params=params, data=body, headers=headers)
            except Exception as e:
                logger.error(f"Exception in request GET {traceback.format_exc()}")

        else: #POST
            headers["Accept"] = "application/json"
            headers["Content-type"] = "application/json"
            headers["User-Agent"] = USER_AGENT
            try:
                # response_dict= await self.aiohttp_request("POST", url, params=params, data=body, headers=headers)
                response_dict= self.python_request("POST", url, params=params, data=body, headers=headers)
                logger.debug(f"response_dict{response_dict}")

                if response_dict and response_dict.get('status'):
                    response_dict['sMsg'] = "Orders placed" 
                    response_dict['status'] = [response_dict['status'],response_dict.get('err_msg',"no error")]
                else:
                    response_dict = {}
                    
            except Exception as e:
                logger.error(f"EXCEPTION IN request POST {traceback.format_exc()}")
                
                response_dict = {}
        logger.debug(time.time()-current_time)
        return response_dict
        

    def python_request(self,method, url, params, data, headers, max_retries = 3):
        try:
            if method.lower() == "post":
                # Send POST request
                logger.debug(f"SENDING {url} , params:{params},data:{data}, headers:{headers}")
                response = requests.post(url, params=params, data=json.dumps(data), headers=headers,timeout=30)

                status_code = response.status_code
                # print(status_code,response.headers)
                rate_limit_remaining = response.headers.get('ratelimit-remaining')
                json_response = response.json()
                # print(json_response)
                json_response['sCode'] = status_code
                json_response['rate_limit_remaining'] = rate_limit_remaining
    
                # # Check if the request was successful (status code 200)
                # if response.status_code == 200:
                #     # If successful, return the JSON response
                #     # print(json_response)
                #     return json_response  # Parse the JSON response from the server
                # else:
                #     # If not successful, log the status and response content
                #     # print(f"Request failed with status code {response.status_code}")
                #     return 
                
                return json_response
            else:

                response = requests.get(url, params=params, data=json.dumps(data), headers=headers)
                rate_limit_remaining = response.headers.get('ratelimit-remaining')

                status_code = response.status_code
                # print(status_code,response)
                json_response = response.json()
                json_response['sCode'] = status_code
                json_response['rate_limit_remaining'] = rate_limit_remaining
    
                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    # If successful, return the JSON response
                    # print(json_response)
                    return json_response  # Parse the JSON response from the server
                else:
                    # If not successful, log the status and response content
                    # print(f"Request failed with status code {response.status_code}")
                    return json_response

        except requests.exceptions.SSLError as ssle:
            logger.error(f"Exception in python_request - SSLERROR:{ssle}")
            # time.sleep(2**i)  # Exponential backoff
            return {}
            
        except requests.exceptions.RequestException as e:
            # If there is any exception with the request
            if response:
                logger.error("ERROR RESPONSE IN PYTHON REQUEST")
            logger.error(f"Exception in python_request {traceback.format_exc()}")
            return {}

        logger.error("Max retires exceeded")

        return {}
    

    async def aiohttp_request(self,method, url, params=None, data=None, headers=None, max_retries=3, timeout=10):
        """Perform an async HTTP request.

        Args:
            method (str): HTTP method ('GET', 'POST', etc.).
            url (str): Target URL.
            params (dict, optional): Query parameters.
            data (dict, optional): JSON request body.
            headers (dict, optional): HTTP headers.
            max_retries (int): Number of retries on failure.
            timeout (int): Timeout in seconds.

        Returns:
            dict: JSON response or empty dict on failure.
        """

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:  # ✅ Auto-closes session
                    async with session.request(
                        method, url, params=params, json=data, headers=headers, timeout=timeout
                    ) as response:
                        json_response = await response.json()
                        json_response["status_code"] = response.status
                        json_response["rate_limit_remaining"] = response.headers.get("ratelimit-remaining")

                        if response.status == 200:
                            return json_response
                        else:
                            logger.error(f"Request failed [{response.status}] {json_response}")

            except aiohttp.ClientError as e:
                print("ERROR")
                logger.error(f"Request attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        logger.error("Max retries exceeded")
        return {}



    # Example usage:
    # response = await aiohttp_request("POST", "https://api.exchange.com/order", params={}, data={"symbol": "BTC-USD"}, headers={})


    def generate_signature(self, method, params, request_path):
        try:
            if request_path.startswith("http://") or request_path.startswith("https://"):
                host_url = urllib.parse.urlparse(request_path).hostname.lower()
                request_path = '/' + '/'.join(request_path.split('/')[3:])
            else:
                host_url = urllib.parse.urlparse(self._host).hostname.lower()
            sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
            encode_params = urllib.parse.urlencode(sorted_params)
            payload = [method, host_url, request_path, encode_params]
            payload = "\n".join(payload)
            payload = payload.encode(encoding="UTF8")
            secret_key = self._secret_key.encode(encoding="utf8")
            digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
            signature = base64.b64encode(digest)
            signature = signature.decode()
            return signature
        except Exception as e:
            logger.error(f"Exception in generate_signature - SSLERROR:{ssle}")



    def format_message(self,input_msg):
        
        # Initialize the output format
        output_msg = {
            "code": "",
            "data": [{
                "clOrdId": "",
                "ordId": "",
                "sCode": "",
                "sMsg": "",
                "tag": "",
                "ts": "",
                "exchange":"htx"
            }],
            "inTime": str(int(time.time() * 1000)),
            "msg": "",
            "outTime": "",
            "rate_limit_remaining":""
        }
        # print('input_msg',input_msg, type(input_msg))
        # print(input_msg['data'],input_msg['sCode'])
        # Check if message is a success or error
        if input_msg['status'][0] == 'ok':
            # Success case
            output_msg['code'] = '0'
            output_msg['data'][0]['ordId'] = input_msg['data']['order_id']
            
            output_msg['data'][0]['sCode'] = input_msg['sCode']
            output_msg['data'][0]['sMsg'] = 'Order placed'
        else:
            
            # Error case
            output_msg['code'] = '1'
            output_msg['data'][0]['errorCode'] = str(input_msg['err_code'])
            output_msg['data'][0]['sCode'] = input_msg['sCode']
            output_msg['data'][0]['sMsg'] = input_msg['err_msg']
            output_msg['msg'] = 'All operations failed'
        output_msg['rate_limit_remaining'] = input_msg['rate_limit_remaining']
        # Add timestamp fields
        output_msg['data'][0]['ts'] = str(input_msg.get('ts', ''))
        output_msg['outTime'] = str(int(time.time() * 1000))
        # print('output_msg',output_msg)
        return output_msg



if __name__ == "__main__":
#     secretKey =fd0bb22e-bg5t6ygr6y-57ca5a15-4ae1f
# apiKey=109e924e-68a4de6a-0fd08753-22dcc
    htx_trade_engine = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",'fd0bb22e-bg5t6ygr6y-57ca5a15-4ae1f','109e924e-68a4de6a-0fd08753-22dcc')
    # loop = asyncio.get_event_loop()
    # result = loop.run_until_complete(
    # htx_trade_engine.get_open_orders('BTC-USD',body = {
    #             "contract_code":"BTC-USD",
    #             # "order_id":123456,
    #             "price":60000,
    #             "created_at":str(datetime.datetime.now()),
    #             "volume":1,
    #             "direction":"buy",
    #             "offset":"open",
    #             "lever_rate":1,
    #             "order_price_type":"limit"
    #             })
    # )
    # loop.close()
    # print(result)


    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
    htx_trade_engine.get_positions('',body = {
                "contract_code":""
                
                })
    )
    loop.close()
    print(result)
    