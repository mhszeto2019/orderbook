#!/bin/bash

# Navigate to the directory where your scripts are located
cd /var/www/html/orderbook || exit 1


echo "Starting auth server..."
bash start_auth_server.sh  &

echo "Starting redis connector..."
bash start_redis_connector.sh  &

echo "Starting Display Engine..."
bash start_display_engine.sh &

echo "Starting Trading Engine..."
bash start_trading_engine.sh &


echo "Starting Algo Engine..."
bash start_algo_engine.sh  &

# Optional: wait for both to finish (remove `&` above if you want them to run sequentially)
wait

echo "All engines started."
