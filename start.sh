#!/bin/bash

# Define logs directory
LOG_DIR="./logs"
mkdir -p $LOG_DIR

# Start each uvicorn server
echo "Starting Uvicorn servers..."

nohup uvicorn app.fastapi.okxperp.rest.public.get_okx_funding_rate:app --port 5001 --reload > $LOG_DIR/okx_funding_rate.log 2>&1 &
echo "OKX funding rate on port 5001"

nohup uvicorn app.fastapi.htxperp.rest.public.get_htx_funding_rate:app --port 5002 --reload > $LOG_DIR/htx_funding_rate.log 2>&1 &
echo "HTX funding rate on port 5002"

nohup uvicorn app.fastapi.htxperp.ws.public.htx_orderbook_ws:app --port 5091 --reload > $LOG_DIR/htx_orderbook_ws.log 2>&1 &
echo "HTX orderbook WS on port 5091"

nohup uvicorn app.fastapi.htxperp.rest.public.get_htx_last_trades:app --port 6101 --reload > $LOG_DIR/htx_last_trades.log 2>&1 &
echo "HTX last trades on port 6101"

nohup uvicorn app.fastapi.okxperp.rest.public.get_okx_last_trades:app --port 6100 --reload > $LOG_DIR/okx_last_trades.log 2>&1 &
echo "OKX last trades on port 6100"

nohup uvicorn app.fastapi.htxperp.rest.private.place_htx_order:app --port 5081 --reload > $LOG_DIR/place_htx_order.log 2>&1 &
echo "HTX place order on port 5081"

nohup uvicorn app.fastapi.okxperp.rest.private.place_okx_order:app --port 5080 --reload > $LOG_DIR/place_okx_order.log 2>&1 &
echo "OKX place order on port 5080"

echo "All servers started."
