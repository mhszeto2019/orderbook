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
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


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
        print("JSON DICT",json_dict)

        return json_dict

    async def place_order(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
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
        # if 'SWAP' not in body['contract_code']:
        #     body['contract_code'] = f"{body['contract_code']}-SWAP"
        json_dict = await self.request("POST", uri, body=body, auth=True)
        json_response2 = self.format_message(json_dict)
        # print("open_orders,json_dict",json_dict)
        # print('json_response2',json_response2)
        return json_response2
    
    async def get_contract_positions(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
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
        print("JSON DICT",json_dict)

        return json_dict

    async def place_contract_order(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
        print('placing contract swap cross order')
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
        print('body',body)
        json_dict = await self.request("POST", uri, body=body, auth=True)
        print(json_dict)
        json_response2 = self.format_message(json_dict)
        # print("open_orders,json_dict",json_dict)
        # print('json_response2',json_response2)
        return json_response2

    async def revoke_order_all(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
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
            print("JSON DICT",json_dict)

            return json_dict

    async def revoke_order(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
            """ Revoke an order.

            Args:
                contract_code: such as "BTC-USD".
                order_id: Order ID.

            Returns:
                success: Success results, otherwise it's None.
                error: Error information, otherwise it's None.
            """
            uri = "/swap-api/v1/swap_cancel"
            # body = {
            #     "contract_code": contract_code
            # }
            # if order_id:
            #     body["order_id"] = order_id
            # if client_order_id:
            #     body["client_order_id"] = client_order_id

            json_dict = await self.request("POST", uri, body=body, auth=True)
            print("JSON DICT",json_dict)
            return json_dict

    async def get_open_orders(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
        # Args:
        #     contract_code: such as "BTC-USD".
        #     index: Page index, default 1st page.
        #     size: Page size, Default 20，no more than 50.

        # Returns:
        #     success: Success results, otherwise it's None.
        #     error: Error information, otherwise it's None.
        uri = "/swap-api/v1/swap_openorders"
        # body = {
        #     "contract_code": contract_code,
        #     "page_index": index,
        #     "page_size": size
        # }
        # body = {}
        json_dict = await self.request("POST", uri, body=body, auth=True)
        return json_dict


    async def get_order_info(self,  symbol,body, order_ids=None, client_order_ids=None):
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

    async def get_tpsl_info(self,  symbol,body, order_id=None, client_order_id=None):
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
    
    async def get_funding_rate(self, symbol,body, index=1, size=50, sort_by='created_at', trade_type=0):
       
        uri = "/swap-api/v1/swap_funding_rate"
       
        json_dict = await self.request("GET", uri, body,  auth=True)
        return json_dict
    
    


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
        if uri.startswith("http://") or uri.startswith("https://"):
            url = uri
        else:
            url = self._host + uri
        if auth:
            timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

            # Encode the timestamp with URI encoding in uppercase
            encoded_timestamp = urllib.parse.quote(timestamp, safe='')

            # print(timestamp,encoded_timestamp)

            params = params if params else {}
            params.update({"AccessKeyId": self._access_key,
                           "SignatureMethod": "HmacSHA256",
                           "SignatureVersion": "2",
                           "Timestamp": timestamp})
            # print(uri)
            # print(params)
            params["Signature"] = self.generate_signature(method, params, uri)
            


        if not headers:
            headers = {}
        if method == "GET":
            headers["Content-type"] = "application/x-www-form-urlencoded"
            headers["User-Agent"] = USER_AGENT
            # _, success, error = await AsyncHttpRequests.fetch("GET", url, params=params, headers=headers, timeout=10)
            try:
                response_dict = self.python_request("GET", url, params=params, data=body, headers=headers)
            except Exception as e:
                print(e)
        else:

            headers["Accept"] = "application/json"
            headers["Content-type"] = "application/json"
            headers["User-Agent"] = USER_AGENT

            # body['contract_code'] =  body['contract_code'].split('-SWAP')[0]

            print(body)
            try:
            
                response_dict= self.python_request("POST", url, params=params, data=body, headers=headers)
                # print('python response',response_dict)
                response_dict['data'] = response_dict.get('data',[])
                response_dict['data']['sMsg'] = 'Orders placed'
                response_dict['status'] = [response_dict['status'],response_dict.get('err_msg',"no error")]

            except Exception as e:
                # print('exception printed',e)
                response_dict = response_dict

        return response_dict
        
    def python_request(self,method, url, params, data, headers):
        import requests

        try:
            if method.lower() == "post":
                # Send POST request
                response = requests.post(url, params=params, data=json.dumps(data), headers=headers)
                status_code = response.status_code
                # print(status_code,response)
                json_response = response.json()
                # print(json_response)
                json_response['sCode'] = status_code

     
                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    # If successful, return the JSON response
                    # print(json_response)
                    return json_response  # Parse the JSON response from the server
                else:
                    # If not successful, log the status and response content
                    # print(f"Request failed with status code {response.status_code}")
                    return json_response
            else:

                response = requests.get(url, params=params, data=json.dumps(data), headers=headers)
                status_code = response.status_code
                # print(status_code,response)
                json_response = response.json()
                # print(json_response)
                json_response['sCode'] = status_code

     
                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    # If successful, return the JSON response
                    # print(json_response)
                    return json_response  # Parse the JSON response from the server
                else:
                    # If not successful, log the status and response content
                    # print(f"Request failed with status code {response.status_code}")
                    return json_response
            
        except requests.exceptions.RequestException as e:
            # If there is any exception with the request
            # print(f"An error occurred: {e}")
            return json_response
    
    def generate_signature(self, method, params, request_path):
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
            "outTime": ""
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
    