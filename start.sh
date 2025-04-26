#!/bin/bash

# Create a new tmux session
tmux new-session -d -s uvicorn_servers -n 'auth' 'source ~/environments/okx/bin/activate && uvicorn app.fastapi.auth:app --port 5001'

# Create windows for public funding rate services
tmux new-window -t uvicorn_servers -n 'okx_funding' 'source ~/environments/okx/bin/activate && uvicorn app.fastapi.okxperp.rest.public.get_okx_funding_rate:app --port 5001  --reload'
tmux new-window -t uvicorn_servers -n 'htx_funding' 'source ~/environments/okx/bin/activate && uvicorn app.fastapi.htxperp.rest.public.get_htx_funding_rate:app --port 5002  --reload'

# Create windows for last trades endpoints
tmux new-window -t uvicorn_servers -n 'htx_trades' 'source ~/environments/okx/bin/activate && uvicorn app.fastapi.htxperp.rest.public.get_htx_last_trades:app --port 6101  --reload'
tmux new-window -t uvicorn_servers -n 'okx_trades' 'source ~/environments/okx/bin/activate && uvicorn app.fastapi.okxperp.rest.public.get_okx_last_trades:app --port 6100  --reload'

# Create window for HTX orderbook websocket
tmux new-window -t uvicorn_servers -n 'htx_orderbook' 'source ~/environments/okx/bin/activate && uvicorn app.fastapi.htxperp.ws.public.htx_orderbook_ws:app --port 5091  --reload'

# Create windows for position endpoints
tmux new-window -t uvicorn_servers -n 'okx_positions' 'source ~/environments/okx/bin/activate && uvicorn app.fastapi.okxperp.rest.private.get_okx_positions:app --port 5070  --reload'
tmux new-window -t uvicorn_servers -n 'htx_positions' 'source ~/environments/okx/bin/activate && uvicorn app.fastapi.htxperp.rest.private.get_htx_positions:app --port 5071  --reload'

# Create windows for order placement
tmux new-window -t uvicorn_servers -n 'place_okx' 'source ~/environments/okx/bin/activate && uvicorn app.fastapi.okxperp.rest.private.place_okx_order:app --port 5080  --reload'
tmux new-window -t uvicorn_servers -n 'place_htx' 'source ~/environments/okx/bin/activate && uvicorn app.fastapi.htxperp.rest.private.place_htx_order:app --port 5081  --reload'

# Create windows for order history
tmux new-window -t uvicorn_servers -n 'okx_orders' 'source ~/environments/okx/bin/activate && uvicorn app.fastapi.okxperp.rest.private.get_okx_orders:app --port 6060  --reload'
tmux new-window -t uvicorn_servers -n 'htx_orders' 'source ~/environments/okx/bin/activate && uvicorn app.fastapi.htxperp.rest.private.get_htx_orders:app --port 6061  --reload'

echo "All services started in tmux session 'uvicorn_servers'"
echo "Attach to the session with: tmux attach -t uvicorn_servers"