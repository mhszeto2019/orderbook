#!/bin/bash

# Source configuration variables from the config folder
source ./config_folder/bashconfig.env

# Define the path to your virtual environment activation script
venv=$VENV_PATH
okxenv=$OKXENV_PATH

# Start a new tmux session for okx_fundingrate_app
# tmux new-session -d -s redis_connector
# tmux send-keys -t redis_connector "source $venv && gunicorn -w 1 -b 0.0.0.0:$REDIS_CONNECTOR_PORT app.redis_connector:app " C-m

tmux new-session -d -s okx_trading_engine
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t okx_trading_engine "source $okxenv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$OKX_TRADING_PORT app.trading_engines.okxTradeApp:app" C-m

tmux new-session -d -s htx_trading_engine
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t htx_trading_engine "source $venv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$HTX_TRADING_PORT app.trading_engines.htxTradeFuturesApp:app" C-m
