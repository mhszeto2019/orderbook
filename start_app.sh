#!/bin/bash

# Activate the virtual environment (optional, if using a virtual environment)
source ~/environments/venv/bin/activate

# Set environment variables (optional)
export APP_ENV=production
export CONFIG_PATH=/project/config_folder

# Change to the application directory (optional)
# cd /project/app/okx

gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:5021 -w 1 app.test.flaskTest:app

gunicorn -k gevent -w 1 --max-requests 1000 --max-requests-jitter 100 -b 0.0.0.0:5000 app.okx2.okx_orderbook_server:app &

gunicorn -k gevent -w 1 --max-requests 1000 --max-requests-jitter 100 -b 0.0.0.0:5001 app.okx2.okx_fundingrate_server:app &

gunicorn -k gevent -w 1 --max-requests 1000 --max-requests-jitter 100 -b 0.0.0.0:5002 app.okx2.okx_spotprice_server:app &

gunicorn -k gevent -w 1 --max-requests 1000 --max-requests-jitter 100 -b 0.0.0.0:5010 app.htx.htx_ladderbook_server:app &

gunicorn -k gevent -w 1 --max-requests 1000 --max-requests-jitter 100 -b 0.0.0.0:5011 app.htx.htx_fundingrate_server:app &

gunicorn -k gevent -w 1 --max-requests 1000 --max-requests-jitter 100 -b 0.0.0.0:5012 app.htx.htx_liveprice_server:app &

# Wait for all background processes to complete
wait


# Optionally, you can redirect output to log files
# gunicorn -k gevent -w 1 -b 0.0.0.0:5002 okx.okx_spotprice_server:app > /path/to/logfile.log 2>&1 &
