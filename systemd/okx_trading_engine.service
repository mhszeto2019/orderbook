#!/bin/bash

# Source configuration variables from the config folder
source /var/www/html/config_folder/bashconfig.env

# Define the path to your virtual environment activation script
venv="/home/brenn/environments/venv"
okxenv="/home/brenn/environments/okx"

pid_folder=$PID_FOLDER

db_port=$DB_PORT

#!/bin/bash

# Configuration variables
OKX_PORT=$OKX_TRADING_PORT   # Replace with actual port
HTX_PORT=$HTX_TRADING_PORT # Replace with actual port
USER="brenn"     # Replace with actual user if needed
GROUP="brenn"    # Replace with actual group if needed

# Service file locations
SERVICE_DIR="/etc/systemd/system"


[Unit]
Description=Gunicorn instance for okx_trading_engine
After=network.target

[Service]
User=brenn
Group=brenn
WorkingDirectory=/var/www/html/orderbook
ExecStart=/home/brenn/environments/okx/bin/gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:5080 --pid /home/brenn/gunicorn_folder/okx_trading_engine.pid --access-logfile /home/brenn/gunicorn_folder/okx_trading_engine_access.log --error-logfile /home/brenn/gunicorn_folder/okx_trading_engine_error.log app.trading_engines.okxTradeApp:app
Environment="VIRTUAL_ENV=/home/brenn/environments/okx"
Environment="PATH=$okxenv:$PATH"
Environment="PYTHONPATH=/var/www/html/orderbook"
Restart=always
RestartSec=10s
StandardOutput=journal
StandardError=journal
TimeoutSec=300

[Install]
WantedBy=multi-user.target
