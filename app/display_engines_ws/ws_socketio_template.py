from flask import Flask
from flask_socketio import SocketIO

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return "Socket.IO Server Running"

# Handle a client connection
@socketio.on('connect')
def handle_connect():
    print("Client connected")
    socketio.emit('server_response', {'message': 'Welcome to the Socket.IO server!'})

# Handle a message from the client
@socketio.on('client_message')
def handle_client_message(data):
    print(f"Received message: {data}")
    response = f"Server received: {data}"
    socketio.emit('server_response', {'message': response})

# Handle client disconnect
@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

if __name__ == '__main__':
    print("Starting Socket.IO server on ws://localhost:5098")
    socketio.run(app, host='localhost', port=5098)
