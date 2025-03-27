#!/bin/bash

# Source configuration variables from the config folder
source ./config_folder/bashconfig.env

# Define the path to your virtual environment activation script
bar=$VENV_PATH

# Start a new tmux session for okx_fundingrate_app
tmux new-session -d -s redis_connector
tmux send-keys -t redis_connector "source $bar && gunicorn -w 1 -b 0.0.0.0:$REDIS_CONNECTOR_PORT app.redis_connector:app " C-m
