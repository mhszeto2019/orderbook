#!/bin/bash
# Define the path to your virtual environment activation script
bar='~/environments/okx/bin/activate'
# Start a new tmux session in detached mode (this avoids "no current client")
tmux new-session -d -s okx_orderbook_app
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t okx_orderbook_app "source $bar && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:5000 app.okx2.okx_orderbook_server:app" C-m

# Detach (optional in this case as we're already detached)
# tmux detach
tmux new-session -d -s okx_fundingrate_app
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t okx_fundingrate_app "source $bar && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:5001 app.okx2.okx_fundingrate_server:app" C-m


tmux new-session -d -s okx_liveprice_app
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t okx_liveprice_app "source $bar && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:5002 app.okx2.okx_spotprice_server:app" C-m

tmux new-session -d -s htx_orderbook_app
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t htx_orderbook_app "source $bar && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:5010 app.htx2.htx_ladderbook_server:app " C-m

tmux new-session -d -s htx_fundingrate_app
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t htx_fundingrate_app "source $bar && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:5011 app.htx2.htx_fundingrate_server:app " C-m

tmux new-session -d -s htx_liveprice_app
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t htx_liveprice_app "source $bar && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:5012 app.htx2.htx_liveprice_server:app " C-m

