#!/bin/bash

# Function to run a FastAPI app with Uvicorn
run_app() {
    APP_PATH=$1
    PORT=$2
    echo "Starting app: $APP_PATH on port $PORT"
    uvicorn $APP_PATH --port $PORT &
}

# Run the first app (get_okx_funding_rate)
run_app "app.fastapi.okxperp.rest.public.get_okx_funding_rate:app " 5001

# run_app "app.fastapi.rest.get_htx_funding_rate:app" 5002


# Run the second app (auth)
run_app "app.fastapi.htxperp.rest.public.get_htx_funding_rate:app" 5000

uvicorn app.fastapi.htxperp.ws.public.htx_orderbook_ws:app --port 5091
uvicorn app.fastapi.okxperp.ws.public.okx_orderbook_ws:app --port 5090


uvicorn app.fastapi.okxperp.rest.public.get_okx_last_trades:app 
python3 app.fastapi.okxperp.rest.public.get_okx_last_trades:app 
# Wait for all background jobs (apps) to finish
wait


uvicorn app.fastapi.auth:app --port 5000
uvicorn app.fastapi.okxperp.rest.public.get_okx_funding_rate:app --port 5001 --host 0.0.0.0  --reload
uvicorn app.fastapi.htxperp.rest.public.get_htx_funding_rate:app --port 5002 --host 0.0.0.0  --reload
uvicorn app.fastapi.htxperp.rest.public.get_htx_last_trades:app --port 6101 --host 0.0.0.0 --reload
uvicorn app.fastapi.okxperp.rest.public.get_okx_last_trades:app --port 6100 --host 0.0.0.0 --reload

uvicorn app.fastapi.htxperp.ws.public.htx_orderbook_ws:app --port 5091 --host 0.0.0.0 --reload

uvicorn app.fastapi.okxperp.rest.private.get_okx_positions:app --port 5070 --host 0.0.0.0 --reload
uvicorn app.fastapi.htxperp.rest.private.get_htx_positions:app --port 5071 --host 0.0.0.0 --reload

uvicorn app.fastapi.okxperp.rest.private.place_okx_order:app --port 5080 --host 0.0.0.0 --reload
uvicorn app.fastapi.htxperp.rest.private.place_htx_order:app --port 5081 --host 0.0.0.0 --reload

 uvicorn app.fastapi.okxperp.rest.private.get_okx_orders:app --port 6060 --host 0.0.0.0 --reload
 uvicorn app.fastapi.htxperp.rest.private.get_htx_orders:app --port 6061 --host 0.0.0.0 --reload



uvicorn app.fastapi.deribitperp.rest.public.get_deribit_funding_rate:app --port 5003
uvicorn app.fastapi.deribitperp.rest.public.get_deribit_last_trades:app --port 6102

uvicorn app.fastapi.deribitperp.rest.private.get_deribit_positions:app --port 5072 --host 0.0.0.0 --reload
uvicorn app.fastapi.deribitperp.rest.private.get_deribit_orders:app --port 6062 --host 0.0.0.0 --reload
uvicorn app.fastapi.deribitperp.rest.private.place_deribit_order:app --port 5082 --host 0.0.0.0 --reload



uvicorn app.fastapi.binanceperp.rest.public.get_binance_funding_rate:app --port 5004
uvicorn app.fastapi.binanceperp.rest.public.get_binance_last_trades:app --port 6103

uvicorn app.fastapi.binanceperp.rest.private.get_binance_positions:app --port 5073 --host 0.0.0.0 --reload

