from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)
process = None  # Global variable to track the subprocess

@app.route('/start-process', methods=['POST'])
def start_process():
    print(request)
    global process
    if process is None or process.poll() is not None:  # Ensure no process is running
        process = subprocess.Popen(["your_command_here"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return jsonify({"message": "Process started", "pid": process.pid}), 200
    else:
        return jsonify({"message": "Process is already running", "pid": process.pid}), 400

@app.route('/stop-process', methods=['POST'])
def stop_process():
    global process
    if process is not None and process.poll() is None:  # Ensure process is running
        process.terminate()  # Politely terminate the process
        process.wait()  # Wait for it to terminate
        process = None
        return jsonify({"message": "Process terminated"}), 200
    else:
        return jsonify({"message": "No process is running"}), 400

if __name__ == '__main__':
    app.run(debug=True,port = 7000)
