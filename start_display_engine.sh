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

htx_display_engine_open_orders_port=$HTX_DISPLAY_OPEN_ORDERS_PORT
okx_display_engine_open_orders_port=$OKX_DISPLAY_OPEN_ORDERS_PORT

htx_display_engine_funding_rate_port=$HTX_DISPLAY_FUNDING_RATE_PORT
okx_display_engine_funding_rate_port=$OKX_DISPLAY_FUNDING_RATE_PORT

htx_display_engine_last_trades_port=$HTX_DISPLAY_LAST_TRADES_PORT
okx_display_engine_last_trades_port=$OKX_DISPLAY_LAST_TRADES_PORT

db_port=$DB_PORT

# Start a new tmux session for okx_fundingrate_app
# tmux new-session -d -s redis_connector
# tmux send-keys -t redis_connector "source $venv && gunicorn -w 1 -b 0.0.0.0:$REDIS_CONNECTOR_PORT app.redis_connector:app " C-m

# ~~~ ORDERBOOK ~~~
tmux new-session -d -s okx_display_engine_orderbook
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t okx_display_engine_orderbook "source $okxenv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$okx_display_engine_orderbook_port --workers 1 app.display_engines_ws.okxbooks:app" C-m

tmux new-session -d -s htx_display_engine_orderbook
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t htx_display_engine_orderbook "source $venv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$htx_display_engine_orderbook_port --workers 1 app.display_engines_ws.htxbooks:app" C-m

# ~~~ ASSETS AND POSIITIONS ~~~
tmux new-session -d -s okx_display_asset_and_position_engine
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t okx_display_asset_and_position_engine "source $okxenv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$okx_display_engine_asset_and_position_port app.display_engines_rest.okx_positions:app" C-m

tmux new-session -d -s htx_display_asset_and_position_engine
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t htx_display_asset_and_position_engine "source $venv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$htx_display_engine_asset_and_position_port app.display_engines_rest.htx_positions:app" C-m

# ~~~ OPEN ORDERS ~~~
# OKX OPEN ORDERS ENGINE NOT REQUIRED because it is with trades
tmux new-session -d -s htx_display_open_orders_engine
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t htx_display_open_orders_engine "source $venv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$htx_display_engine_open_orders_port app.display_engines_rest.htx_open_orders:app --log-level info" C-m

# ~~~ FUNDING RATE~~~
tmux new-session -d -s okx_funding_rate
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t okx_funding_rate "source $okxenv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers=1 -b 0.0.0.0:$okx_display_engine_funding_rate_port app.display_engines_rest.get_okx_funding_rate:app --log-level info" C-m

tmux new-session -d -s htx_funding_rate
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t htx_funding_rate "source $venv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers=1 -b 0.0.0.0:$htx_display_engine_funding_rate_port app.display_engines_rest.get_htx_funding_rate:app --log-level info" C-m

# ~~~ LAST TRADES BY PUBLIC ~~~
tmux new-session -d -s okx_last_public_trades
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t okx_last_public_trades "source $okxenv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$okx_display_engine_last_trades_port app.display_engines_rest.get_okx_trade_history:app --log-level info" C-m

tmux new-session -d -s htx_last_public_trades
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t htx_last_public_trades "source $venv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers=1 -b 0.0.0.0:$htx_display_engine_last_trades_port app.display_engines_ws.htx_trade_history:app --log-level info" C-m

tmux new-session -d -s db_connection
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t db_connection "source $okxenv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers=1 -b 0.0.0.0:$db_port app.db.db_connection:app --log-level info" C-m

