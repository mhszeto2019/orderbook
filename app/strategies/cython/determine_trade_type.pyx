# cython: language_level=3
from libc.stdlib cimport abs
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)
def determine_trade_type(dict algo_json_dict):
    cdef int net_availability = int(algo_json_dict.get('net_availability', 0))
    cdef int total_buy = 0
    cdef int total_sell = 0
    cdef int diaoyu_buy = 0
    cdef int diaoyu_sell = 0
    cdef int diaoxia_buy = 0
    cdef int diaoxia_sell = 0
    cdef str algo_type
    cdef str algo_name
    cdef dict stats

    for algo_type, algos in algo_json_dict.items():
        if algo_type == 'net_availability':
            continue
        for algo_name, stats in algos.items():
            if stats.get('status', False):
                buy = stats.get('buy', 0) - stats.get('filled_amount', 0)
                sell = stats.get('sell', 0) - stats.get('filled_amount', 0)

                total_buy += buy
                total_sell += sell

                if algo_type == 'diaoyu':
                    diaoyu_buy += buy
                    diaoyu_sell += sell
                elif algo_type == 'diaoxia':
                    diaoxia_buy += buy
                    diaoxia_sell += sell

    remaining_pos = net_availability + diaoyu_buy - diaoyu_sell

    trade_type = {"buy": None, "sell": "open"}

    if net_availability < 0 and diaoxia_buy > 0:
        if abs(remaining_pos) >= diaoxia_buy:
            trade_type["buy"] = "close"
    elif net_availability > 0 and diaoxia_sell > 0:
        if remaining_pos >= diaoxia_sell:
            trade_type["sell"] = "close"
    elif net_availability == 0:
        trade_type["buy"] = "open"
        trade_type["sell"] = "open"

    return trade_type
