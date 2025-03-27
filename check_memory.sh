#!/bin/bash

# Memory threshold in MB
MEMORY_LIMIT=500

# Function to check memory usage
check_memory() {
    session=$1
    tmux list-panes -t $session -F "#{pane_pid}" 2>/dev/null | while read pid; do
        if [ -z "$pid" ]; then
            echo "Session $session not running."
            return
        fi

        memory_usage=$(pmap $pid | tail -n 1 | awk '/[0-9]K/{print $2}' | sed 's/K//')
        memory_usage_mb=$((memory_usage / 1024))

        cpu_usage=$(ps -p $pid -o %cpu --no-headers)
        cpu_usage=${cpu_usage%.*} # Truncate decimal point if exists

        echo "Session: $session, PID: $pid, CPU Usage: $cpu_usage%, Memory Usage: ${memory_usage_mb}MB"

        if [ "$memory_usage_mb" -gt "$MEMORY_LIMIT" ]; then
            echo "Restarting $session due to high memory usage: ${memory_usage_mb}MB"
            tmux kill-session -t $session
            tmux new-session -d -s $session
        fi
    done
}

# Add your tmux sessions here
check_memory "okx_display_engine_orderbook"
check_memory "htx_display_engine_orderbook"
check_memory "htx_trading_engine"
check_memory "okx_display_engine_orderbook"
check_memory "htx_display_open_orders_engine"
check_memory "auth_server"
check_memory "redis_connector"
check_memory "htx_display_asset_and_position_engine"
check_memory "okx_display_asset_and_position_engine"
