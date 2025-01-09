#!/bin/bash

# Source configuration variables from the config folder
source ./config_folder/bashconfig.env

# Define the path to your virtual environment activation script
venv=$VENV_PATH
okxenv=$OKXENV_PATH


tmux new-session -d -s algo_factory
# Create a new window within that session, ensuring the environment is sourced
tmux send-keys -t algo_factory "source $okxenv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers=1 -b 0.0.0.0:$ALGO_PORT app.strategies.algo_factory:app" C-m
