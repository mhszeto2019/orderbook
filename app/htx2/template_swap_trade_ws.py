#!/usr/bin/env python

import datetime
import uuid
import urllib
import asyncio
import websockets
import json
import hmac
import base64
import hashlib
import gzip
import traceback

        

def generate_signature(host, method, params, request_path, secret_key):
    """Generate signature of huobi future.
    
    Args:
        host: api domain url.PS: colo user should set this host as 'api.hbdm.com',not colo domain.
        method: request method.
        params: request params.
        request_path: "/notification"
        secret_key: api secret_key

    Returns:
        singature string.

    """
    host_url = urllib.parse.urlparse(host).hostname.lower()
    sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
    encode_params = urllib.parse.urlencode(sorted_params)
    payload = [method, host_url, request_path, encode_params]
    payload = "\n".join(payload)
    payload = payload.encode(encoding="UTF8")
    secret_key = secret_key.encode(encoding="utf8")
    digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(digest)
    signature = signature.decode()
    return signature

async def subscribe(url, access_key, secret_key, subs, callback=None, auth=False):
    """ Huobi Future subscribe websockets.

    Args:
        url: the url to be signatured.
        access_key: API access_key.
        secret_key: API secret_key.
        subs: the data list to subscribe.
        callback: the callback function to handle the ws data received. 
        auth: True: Need to be signatured. False: No need to be signatured.

    """
    async with websockets.connect(url) as websocket:
        if auth:
            timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            data = {
                "AccessKeyId": access_key,
                "SignatureMethod": "HmacSHA256",
                "SignatureVersion": "2",
                "Timestamp": timestamp
            }
            # sign = generate_signature(url,"GET", data, "/swap-trade", secret_key)
            sign = generate_signature(url,"GET", data, "/swap-notification", secret_key)

            data["op"] = "auth"
            data["type"] = "api"
            data["Signature"] = sign
            msg_str = json.dumps(data)
            await websocket.send(msg_str)
            print(f"send: {msg_str}")
        for sub in subs:
            sub_str = json.dumps(sub)
            await websocket.send(sub_str)
            print(f"send: {sub_str}")
        while True:
            rsp = await websocket.recv()
            data = json.loads(gzip.decompress(rsp).decode())
            print(f"recevie<--: {data}")
            if "op" in data and data.get("op") == "ping":
                pong_msg = {"op": "pong", "ts": data.get("ts")}
                await websocket.send(json.dumps(pong_msg))
                print(f"send: {pong_msg}")
                continue
            if "ping" in data: 
                pong_msg = {"pong": data.get("ping")}
                await websocket.send(json.dumps(pong_msg))
                print(f"send: {pong_msg}")
                continue
            rsp = await callback(data)

async def handle_ws_data(*args, **kwargs):
    """ callback function
    Args:
        args: values
        kwargs: key-values.
    """
    # print("callback param", *args,**kwargs)

if __name__ == "__main__":
    ####  input your access_key and secret_key below:
    access_key = ""
    secret_key = ""

    # market_url = 'ws://api.hbdm.vn/linear-swap-ws'
    order_url = 'wss://api.hbdm.com/swap-notification'
    
    # market_subs = [
                   
    #             {
    #                 "sub": "market.BTC-USDT.kline.1min.open",
    #                 "id": "id1"
    #             },
    #             {
    #                 "sub": "market.BTC-USDT.depth.step0",
    #                 "id": "id1"
    #             }

    #         ]
    order_subs = [
                # {
                #     "op": "sub",
                #     "cid": str(uuid.uuid1()),
                #     "topic": "orders.BTC-USD"
                # },
                {
                    "op": "sub",
                    "cid": str(uuid.uuid1()),
                    "topic": "positions.BTC-USD"
                }

            ]

    place_order_url = "wss://api.hbdm.com/swap-trade"
    place_order_subs= [
            {
            "op":"create_order",
            "cid":str(uuid.uuid1()),
            "data":{"contract_code":"BTC-USD",
                    "price":"106703",
                    "volume":"1",
                    "direction":"buy",
                    "offset":"open",
                    "lever_rate":5,
                    "order_price_type":"limit"
                    }
            }
    ]

    while True: 
        try:
            asyncio.get_event_loop().run_until_complete(subscribe(order_url, access_key,  secret_key, order_subs, handle_ws_data, auth=True))
            # asyncio.get_event_loop().run_until_complete(subscribe(place_order_url, access_key,  secret_key, place_order_subs, handle_ws_data, auth=True))
        #except (websockets.exceptions.ConnectionClosed):
        except Exception as e:
            traceback.print_exc()
            print('websocket connection error. reconnect rightnow')



# recevie<--: {'op': 'notify', 'topic': 'orders.btc-usd', 'ts': 1734410654405, 'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1, 'price': 106426, 'order_price_type': 'limit', 'direction': 'buy', 'offset': 'open', 'status': 3, 'lever_rate': 5, 'order_id': 1318559382298243072, 'order_id_str': '1318559382298243072', 'client_order_id': None, 'order_source': 'web', 'order_type': 1, 'created_at': 1734410654384, 'trade_volume': 0, 'trade_turnover': 0, 'fee': 0, 'trade_avg_price': 0, 'margin_frozen': 0.000187924003532971, 'profit': 0, 'trade': [], 'canceled_at': 0, 'fee_asset': 'BTC', 'uid': '502448972', 'liquidation_type': '0', 'is_tpsl': 0, 'real_profit': 0}
# callback param {'op': 'notify', 'topic': 'orders.btc-usd', 'ts': 1734410654405, 'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1, 'price': 106426, 'order_price_type': 'limit', 'direction': 'buy', 'offset': 'open', 'status': 3, 'lever_rate': 5, 'order_id': 1318559382298243072, 'order_id_str': '1318559382298243072', 'client_order_id': None, 'order_source': 'web', 'order_type': 1, 'created_at': 1734410654384, 'trade_volume': 0, 'trade_turnover': 0, 'fee': 0, 'trade_avg_price': 0, 'margin_frozen': 0.000187924003532971, 'profit': 0, 'trade': [], 'canceled_at': 0, 'fee_asset': 'BTC', 'uid': '502448972', 'liquidation_type': '0', 'is_tpsl': 0, 'real_profit': 0}
# recevie<--: {'op': 'ping', 'ts': '1734410655315'}
# send: {'op': 'pong', 'ts': '1734410655315'}

# LIMIT ORDER TO POSITION
# recevie<--: {'op': 'notify', 'topic': 'orders.btc-usd', 'ts': 1734410815118, 'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1, 'price': 106587, 'order_price_type': 'limit', 'direction': 'buy', 'offset': 'open', 'status': 6, 'lever_rate': 5, 'order_id': 1318559941178667008, 'order_id_str': '1318559941178667008', 'client_order_id': None, 'order_source': 'web', 'order_type': 1, 'created_at': 1734410787632, 'trade_volume': 1, 'trade_turnover': 100.0, 'fee': 2.8146021559e-08, 'trade_avg_price': 106587.00000000006, 'margin_frozen': 0.0, 'profit': 0, 'trade': [{'trade_fee': 2.8146021559e-08, 'fee_asset': 'BTC', 'real_profit': 0, 'profit': 0, 'trade_id': 100002460772968, 'id': '100002460772968-1318559941178667008-1', 'trade_volume': 1, 'trade_price': 106587, 'trade_turnover': 100.0, 'created_at': 1734410815099, 'role': 'maker'}], 'canceled_at': 0, 'fee_asset': 'BTC', 'uid': '502448972', 'liquidation_type': '0', 'is_tpsl': 0, 'real_profit': 0}
# callback param {'op': 'notify', 'topic': 'orders.btc-usd', 'ts': 1734410815118, 'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1, 'price': 106587, 'order_price_type': 'limit', 'direction': 'buy', 'offset': 'open', 'status': 6, 'lever_rate': 5, 'order_id': 1318559941178667008, 'order_id_str': '1318559941178667008', 'client_order_id': None, 'order_source': 'web', 'order_type': 1, 'created_at': 1734410787632, 'trade_volume': 1, 'trade_turnover': 100.0, 'fee': 2.8146021559e-08, 'trade_avg_price': 106587.00000000006, 'margin_frozen': 0.0, 'profit': 0, 'trade': [{'trade_fee': 2.8146021559e-08, 'fee_asset': 'BTC', 'real_profit': 0, 'profit': 0, 'trade_id': 100002460772968, 'id': '100002460772968-1318559941178667008-1', 'trade_volume': 1, 'trade_price': 106587, 'trade_turnover': 100.0, 'created_at': 1734410815099, 'role': 'maker'}], 'canceled_at': 0, 'fee_asset': 'BTC', 'uid': '502448972', 'liquidation_type': '0', 'is_tpsl': 0, 'real_profit': 0}
# recevie<--: {'op': 'ping', 'ts': '1734410817396'}

# CLOSE POSITION
# recevie<--: {'op': 'notify', 'topic': 'orders.btc-usd', 'ts': 1734410838874, 'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1.0, 'price': 0, 'order_price_type': 'market', 'direction': 'sell', 'offset': 'close', 'status': 6, 'lever_rate': 5, 'order_id': 1318560155979558912, 'order_id_str': '1318560155979558912', 'client_order_id': None, 'order_source': 'web', 'order_type': 1, 'created_at': 1734410838790, 'trade_volume': 1, 'trade_turnover': 100.0, 'fee': -3.00415888245e-07, 'trade_avg_price': 106519.0000000001, 'margin_frozen': 0, 'profit': -5.989321048e-07, 'trade': [{'trade_fee': -3.00415888245e-07, 'fee_asset': 'BTC', 'real_profit': -5.989321048e-07, 'profit': -5.989321048e-07, 'trade_id': 100002460773958, 'id': '100002460773958-1318560155979558912-1', 'trade_volume': 1, 'trade_price': 106519, 'trade_turnover': 100.0, 'created_at': 1734410838856, 'role': 'taker'}], 'canceled_at': 0, 'fee_asset': 'BTC', 'uid': '502448972', 'liquidation_type': '0', 'is_tpsl': 0, 'real_profit': -5.989321048e-07}
# callback param {'op': 'notify', 'topic': 'orders.btc-usd', 'ts': 1734410838874, 'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1.0, 'price': 0, 'order_price_type': 'market', 'direction': 'sell', 'offset': 'close', 'status': 6, 'lever_rate': 5, 'order_id': 1318560155979558912, 'order_id_str': '1318560155979558912', 'client_order_id': None, 'order_source': 'web', 'order_type': 1, 'created_at': 1734410838790, 'trade_volume': 1, 'trade_turnover': 100.0, 'fee': -3.00415888245e-07, 'trade_avg_price': 106519.0000000001, 'margin_frozen': 0, 'profit': -5.989321048e-07, 'trade': [{'trade_fee': -3.00415888245e-07, 'fee_asset': 'BTC', 'real_profit': -5.989321048e-07, 'profit': -5.989321048e-07, 'trade_id': 100002460773958, 'id': '100002460773958-1318560155979558912-1', 'trade_volume': 1, 'trade_price': 106519, 'trade_turnover': 100.0, 'created_at': 1734410838856, 'role': 'taker'}], 'canceled_at': 0, 'fee_asset': 'BTC', 'uid': '502448972', 'liquidation_type': '0', 'is_tpsl': 0, 'real_profit': -5.989321048e-07}

# order.match
# {'op': 'notify', 'topic': 'positions.btc-usd', 'ts': 1734419182416, 'event': 'order.match', 'data': [{'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1.0, 'available': 1.0, 'frozen': 0.0, 'cost_open': 106745.10000000002, 'cost_hold': 106745.10000000002, 'profit_unreal': 7.72237654e-08, 'profit_rate': 0.00041216292800446, 'profit': 7.72237654e-08, 'position_margin': 0.000187346785457018, 'lever_rate': 5, 'direction': 'buy', 'last_price': 106753.9, 'adl_risk_percent': 1}], 'uid': '502448972'}