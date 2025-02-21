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

# This will keep track of when the app started

# Simulating a long-running process that will update the status
def update_status2(msg):
    # Here, you can update the app_status dictionary with live data (e.g., after a trade)
    # For example, update the last trade action:
    print(msg)
    app_status['last_trade_action'] = msg
    app_status['last_log_entry'] = "Trade executed at {}".format(time.strftime('%Y-%m-%d %H:%M:%S'))
    app_status['uptime'] = int(time.time() - app_status['start_time'])  # Update uptime
    app_status['start_time'] = time.time()


@app.route('/')
def home():
    return render_template('status.html', app_status=app_status)

@app.route('/status')
def status():
    # update_status()  # Update the status
    print(app_status)
    return jsonify(app_status)  # Return status as JSON to the frontend for AJAX updates

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
