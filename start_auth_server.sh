#!/bin/bash

# Source configuration variables from the config folder
source ./config_folder/bashconfig.env

# Define the path to your virtual environment activation script
bar=$VENV_PATH

# # Start a new tmux session for okx_orderbook_app
# tmux new-session -d -s okx_orderbook_app
# tmux send-keys -t okx_orderbook_app "source $bar && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$OKX_ORDERBOOK_PORT app.okx2.okx_orderbook_server:app" C-m

# Start a new tmux session for auth_server
tmux new-session -d -s auth_server
tmux send-keys -t auth_server "source $bar && gunicorn -w 1 -b 0.0.0.0:$AUTH_PORT app.auth:app " C-m
