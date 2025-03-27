# Kill processes running on ports 5000, 5001, 5010, 5011, and 5012
pkill -f tmux
lsof -i:5000 -i:5001 -i:5002 -i:5010 -i:5011 -i:5012 -t | xargs kill

