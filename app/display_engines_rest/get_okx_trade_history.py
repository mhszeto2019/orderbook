import okx.MarketData as MarketData

flag = "0"  # Production trading:0 , demo trading:1

marketDataAPI =  MarketData.MarketAPI(flag=flag)

# Retrieve the recent transactions of an instrument from the last 3 months with pagination
result = marketDataAPI.get_history_trades(
    instId="BTC-USD-SWAP"
)
# print(result)
# print(result['data'])
for row in result['data']:
    print(row)
