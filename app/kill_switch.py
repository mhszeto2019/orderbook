from flask import Flask, request, jsonify
import threading
import time
import os
import signal

app = Flask(__name__)

# Global variable to track if the task is running
task_thread = None
shutdown_flag = False

# Background function
def background_task():
    global shutdown_flag
    while not shutdown_flag:
        print("Running task...")
        time.sleep(2)  # Simulate work

# Start the task
@app.route('/start', methods=['POST'])
def start():
    global task_thread, shutdown_flag
    if task_thread and task_thread.is_alive():
        return jsonify({"message": "Task is already running"}), 400

    shutdown_flag = False
    task_thread = threading.Thread(target=background_task)
    task_thread.start()

    return jsonify({"message": "Task started"}), 200

# Stop the task and Flask server
@app.route('/shutdown', methods=['POST'])
def shutdown():
    global shutdown_flag
    shutdown_flag = True
    os.kill(os.getpid(), signal.SIGINT)  # Kill the process
    return jsonify({"message": "Shutting down server"}), 200

# Check if task is running
@app.route('/status', methods=['GET'])
def status():
    global task_thread
    return jsonify({"running": task_thread.is_alive() if task_thread else False}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5099)
