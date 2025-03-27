#!/bin/bash
# Kill all processes containing "trading_engine" in their command line
tmux list-sessions | grep "trading_engine" | awk -F: '{print $1}' | xargs -I {} tmux kill-session -t {}

# Kill processes running on ports 5080 and 5081
lsof -i:5080 -i:5081 -t | xargs kill