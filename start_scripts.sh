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

