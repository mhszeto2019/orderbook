#!/bin/bash
# Kill all processes containing "trading_engine" in their command line
tmux list-sessions | grep "display" | awk -F: '{print $1}' | xargs -I {} tmux kill-session -t {}

# Kill processes running on ports 5080 and 5081
lsof -i:5090 -i:5091 -i:5070 -i:5071 -t | xargs kill