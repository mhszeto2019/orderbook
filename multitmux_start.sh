#!/bin/bash
tmux new-session -d -s app_session 'gunicorn -k gevent -w 3 --max-requests 1000 --max-requests-jitter 100 -b 0.0.0.0:5002 app.okx.okx_spotprice_server:app'
tmux new-window -t app_session:1 'gunicorn -k gevent -w 3 --max-requests 1000 --max-requests-jitter 100 -b 0.0.0.0:5003 app.okx.okx_spotprice_server:app'
tmux new-window -t app_session:2 'gunicorn -k gevent -w 3 --max-requests 1000 --max-requests-jitter 100 -b 0.0.0.0:5004 app.okx.okx_spotprice_server:app'
tmux attach-session -t app_session
