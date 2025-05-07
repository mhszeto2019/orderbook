#!/bin/bash

# Source the configuration variables from the config folder
# CHANGE HOME FILE
source /var/www/html/orderbook/config_folder/bashconfig.env

# Define the path to your virtual environment activation script
venv="$HOME/environments/venv"
okxenv="$HOME/environments/okx"

# Directories for storing PID files and logs
PID_FOLDER="$HOME/gunicorn_folder"
USER=$USER
GROUP=$GROUP
SERVICE_DIR="/var/www/html/orderbook/systemd" 
# AUTH_PORT=5000
# REDIS_CONNECTOR_PORT=6001

# List of services with corresponding port variables
declare -A SERVICES_PORTS
SERVICES_PORTS=(

  # ["htx_positions"]=$HTX_DISPLAY_ASSET_AND_POSITION_PORT #REST
  # ["htx_open_orders"]=$HTX_DISPLAY_OPEN_ORDERS_PORT #REST

  ["get_htx_positions"]=$HTX_DISPLAY_ASSET_AND_POSITION_PORT #REST
  ["get_htx_orders"]=$HTX_DISPLAY_OPEN_ORDERS_PORT #REST
  ["place_htx_order"]=$HTX_TRADING_PORT


)

# Loop through the services and create systemd files
for SERVICE_NAME in "${!SERVICES_PORTS[@]}"; do
 echo "Service: $SERVICE_NAME, Port: '${SERVICES_PORTS[$SERVICE_NAME]}'"
  PORT=${SERVICES_PORTS[$SERVICE_NAME]}
    ENV_PATH="$okxenv"
    ENV_PATH_STR="\$okxenv"  # Use the okxenv environment for okx services

  
  # Check if the service file already exists in the systemd folder, and delete it if it does
  if [ -f "$SERVICE_DIR/$SERVICE_NAME.service" ]; then
    echo "Deleting existing service file: $SERVICE_DIR/$SERVICE_NAME.service"
    sudo rm "$SERVICE_DIR/$SERVICE_NAME.service"
  fi
  
  # Create the systemd service file for each service in /var/www/html/orderbook/systemd
  cat <<EOF > "$SERVICE_DIR/$SERVICE_NAME.service"

source /var/www/html/config_folder/bashconfig.env
venv="$HOME/environments/venv"
okxenv="$HOME/environments/okx"

[Unit]
Description=Uvicorn instance for $SERVICE_NAME
After=network.target

[Service]
User=$USER
Group=$GROUP
WorkingDirectory=/var/www/html/orderbook
ExecStart=$ENV_PATH/bin/uvicorn app.fastapi.htxperp.rest.private.$SERVICE_NAME:app --port $PORT --host 0.0.0.0 
Environment="VIRTUAL_ENV=$ENV_PATH"
Environment="PATH=$ENV_PATH_STR:\$PATH"
Environment="PYTHONPATH=/var/www/html/orderbook"
Restart=always
RestartSec=10s
StandardOutput=journal
StandardError=journal
TimeoutSec=300

[Install]
WantedBy=multi-user.target
EOF

  # Print to the user that the service file was created
  echo "Service file created for $SERVICE_NAME at $SERVICE_DIR/$SERVICE_NAME.service"
  
  # Symlink the service file from /var/www/html/orderbook/systemd to /etc/systemd/system
  sudo ln -sf "$SERVICE_DIR/$SERVICE_NAME.service" "/etc/systemd/system/$SERVICE_NAME.service"

  # Reload systemd, enable, and start the service
  sudo systemctl daemon-reload
  sudo systemctl enable $SERVICE_NAME.service
  sudo systemctl start $SERVICE_NAME.service

  echo "Started $SERVICE_NAME service."
done

echo "All services have been created, enabled, and started."