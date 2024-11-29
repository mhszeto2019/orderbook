#!/bin/bash

# Source configuration variables from the config folder
source ./config_folder/bashconfig.env

# Define the path to your virtual environment activation script
venv=$VENV_PATH
okxenv=$OKXENV_PATH
htx_display_engine_orderbook_port=$HTX_DISPLAY_ORDERBOOK_PORT
okx_display_engine_orderbook_port=$OKX_DISPLAY_ORDERBOOK_PORT

htx_display_engine_asset_and_position_port=$HTX_DISPLAY_ASSET_AND_POSITION_PORT
okx_display_engine_asset_and_position_port=$OKX_DISPLAY_ASSET_AND_POSITION_PORT
# Start a new tmux session for okx_fundingrate_app
# tmux new-session -d -s redis_connector
# tmux send-keys -t redis_connector "source $venv && gunicorn -w 1 -b 0.0.0.0:$REDIS_CONNECTOR_PORT app.redis_connector:app " C-m

tmux new-session -d -s okx_display_engine_orderbook
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t okx_display_engine_orderbook "source $okxenv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$okx_display_engine_orderbook_port --workers 1 app.display_engines_ws.okxbooks:app" C-m

tmux new-session -d -s htx_display_engine_orderbook
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t htx_display_engine_orderbook "source $venv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$htx_display_engine_orderbook_port --workers 1 app.display_engines_ws.htxbooks:app" C-m

# tmux new-session -d -s okx_display_asset_and_position_engine
# # Create a new window within that session, ensuring the environment is sourced
# tmux send-keys -t okx_display_asset_and_position_engine "source $okxenv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$okx_display_engine_asset_and_position_port app.display_engines_ws.okxbooks:app" C-m

# tmux new-session -d -s htx_display_asset_and_position_engine
# # Create a new window within that session, ensuring the environment is sourced
# tmux send-keys -t htx_display_asset_and_position_engine "source $venv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$htx_display_engine_asset_and_position_port app.display_engines_ws.htxbooks:app" C-m