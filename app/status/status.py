from flask import Flask, render_template, jsonify
import time
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
CORS(app)

# Initial status of the app
app_status = {
    "status": "Running",         # General status of the app (e.g., 'Running', 'Error')
    "uptime": 0,                 # Uptime in seconds
    "last_trade_action": "None", # Last trade action (e.g., 'buy okx sell htx')
    "last_log_entry": "None"     # Last log entry (optional)
}
class Status:
    def __init__(self):
        self.exchange = None,
        self.direction = None,
        self.status = None,
        self.uptime = None
    
    def update_status(self,exchange,direction,status):
        self.exchange = exchange,
        self.direction = direction,
        self.status = status
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
