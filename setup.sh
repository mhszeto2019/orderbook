#!/bin/bash

# Ensure virtualenv is installed
if ! command -v virtualenv &> /dev/null; then
    echo "virtualenv not found. Installing..."
    pip install virtualenv
fi

# Create environments directory if it doesn't exist
mkdir -p ~/environments

# Create Virtual Environments (if not already created)
if [ ! -d "~/environments/okx" ]; then
    virtualenv ~/environments/okx
fi

if [ ! -d "~/environments/venv" ]; then
    virtualenv ~/environments/venv
fi

# Activate and install requirements for OKX
echo "Activating OKX environment and installing dependencies..."
source ~/environments/okx/bin/activate
pip install -r /var/www/html/orderbook/requirements_okx.txt
deactivate

# Activate and install requirements for VENV
echo "Activating VENV environment and installing dependencies..."
source ~/environments/venv/bin/activate
pip install -r /var/www/html/orderbook/requirements_venv.txt
deactivate

echo "Setup completed successfully!"
