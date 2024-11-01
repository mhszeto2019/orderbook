import gzip
import json
import datetime

def decoder(binary_code):
    uncoded_msg = gzip.decompress(binary_code).decode("utf-8")
    json_uncoded = json.loads(uncoded_msg)
    return json_uncoded


def unix_ts_to_datetime(unix_ts):
    if isinstance(unix_ts, str):
        unix_ts = int(unix_ts)
    # Check if the timestamp is in milliseconds and convert if necessary
    if len(str(unix_ts)) > 10:  # Assuming timestamps longer than 10 digits are in milliseconds
        unix_ts /= 1000
    # Convert the timestamp to a datetime string
    ts = datetime.datetime.fromtimestamp(unix_ts).strftime('%Y-%m-%d%H:%M:%S')
    # print(ts)  # This will print the converted date and time
    return ts

def standardised_ccy_naming(ccy):
    
    ccy = ccy.lower()
    ccy = ccy.replace('-','')
    ccy = ccy.replace('_','')
    # print("Convert {} to {}".format(ccy,ccy))
    return ccy
    
def mapping_for_ccy(standardised_ccy):
    if standardised_ccy in {"btc_cw","btcusdswap"}:
        return str("btc_coinmargin")
    else:
        return standardised_ccy
    
def format_arr_4dp(arr):
    formatted_arr = [
    [f"{float(ele[0]):.4f}", f"{float(ele[1]):.4f}"]  # Format both price and quantity
    for ele in arr
]
    return formatted_arr

def format_arr_1dp(arr):
    formatted_arr = [
    [f"{float(ele[0]):.1f}", f"{float(ele[1]):.1f}"]  # Format both price and quantity
    for ele in arr
]
    return formatted_arr