async def cancel_all_htx_open_order_by_ccy():
    try:
    
        data = request.get_json()
        username = data.get('username')
        # Get the order data from the request
        # okx_secretkey_apikey_passphrase = r.get('user:test123d:api_credentials"')
        key_string = data.get('redis_key')
        if key_string.startswith("b'") and key_string.endswith("'"):
            cleaned_key_string = key_string[2:-1]
        else:
            cleaned_key_string = key_string  # Fallback if the format is unexpected
        # Now decode the base64 string into bytes
        key_bytes = base64.urlsafe_b64decode(cleaned_key_string)
        key_bytes = cleaned_key_string.encode('utf-8')
        # You can now use the key with Fernet
        cipher_suite = Fernet(key_bytes)
        
        cache_key = f"user:{username}:api_credentials"
        # Fetch the encrypted credentials from Redis
        encrypted_data = r.get(cache_key)   
        
        if encrypted_data:
        # Decrypt the credentials
            decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
            api_creds_dict = json.loads(decrypted_data)
            

        # Data received from the client (assuming JSON body)
        instId = data.get('ccy','')
        # instId= data["instId"].replace("-SWAP", "")
        tdMode= "cross"
        # Extract necessary parameters from the request
        # tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_secretkey'],api_creds_dict['htx_apikey'])
        tradeApi = HuobiCoinFutureRestTradeAPI("https://api.hbdm.com",api_creds_dict['htx_apikey'],api_creds_dict['htx_secretkey'])

        open_orders_request = await tradeApi.revoke_order_all(
            instId,body = {
            "contract_code": instId
            }
        )

        return open_orders_request
    
    except Exception as e:
        logger.error(e)

def cancel_all_orders_by_ccy():
    try:
        data = request.get_json()
        username = data.get('username')
        key_string = data.get('redis_key')
        if key_string.startswith("b'") and key_string.endswith("'"):
            cleaned_key_string = key_string[2:-1]
        else:
            cleaned_key_string = key_string  # Fallback if the format is unexpected
        key_bytes = base64.urlsafe_b64decode(cleaned_key_string)
        key_bytes = cleaned_key_string.encode('utf-8')
        # You can now use the key with Fernet
        cipher_suite = Fernet(key_bytes)
        
        cache_key = f"user:{username}:api_credentials"
        # Fetch the encrypted credentials from Redis
        encrypted_data = r.get(cache_key)   
        if encrypted_data:
        # Decrypt the credentials
            decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
            api_creds_dict = json.loads(decrypted_data)
            print(f"API credentials for {username}", api_creds_dict)
        tradeAPI = Trade.TradeAPI(api_creds_dict['okx_apikey'], api_creds_dict['okx_secretkey'], api_creds_dict['okx_passphrase'], False, '0')
        response = tradeAPI.get_order_list(instId=data['ccy'])
        
        # # print(data)
        print('order_list',response['data'])
        order_list = []
        for row in response['data']:
            order_list.append({"instId":row['instId'], "ordId":row['ordId']})
        result = tradeAPI.cancel_multiple_orders(order_list)
        print('result',result)
        if len(result.get('data')) == 0:
            print('fail')
            return result
        return result
    
    except Exception as e:
        print(e)