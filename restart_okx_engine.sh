#!/bin/bash

okxenv=$OKXENV_PATH
okx_display_engine_orderbook_port=$OKX_DISPLAY_ORDERBOOK_PORT

#!/bin/bash
while true; do
    # Check if gunicorn is running
    if ! pgrep -x "gunicorn" > /dev/null; then
        echo "gunicorn is not running, restarting..."
        tmux send-keys -t okx_display_engine_orderbook "source $okxenv && gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$okx_display_engine_orderbook_port --workers 1 app.display_engines_ws.okxbooks:app" C-m
    fi
    sleep 5
done

