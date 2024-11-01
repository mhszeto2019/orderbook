#!/bin/bash
# Define the path to your virtual environment activation script
bar='~/environments/okx/bin/activate'
# Start a new tmux session in detached mode (this avoids "no current client")
tmux new-session -d -s assets_positions
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t assets_positions "source $bar && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:5023 app.test.flaskTest:app" C-m

# tmux detach
tmux new-session -d -s okx_fundingrate_app
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t okx_fundingrate_app "source $bar && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:5022 app.test.txnHistory:app" C-m

