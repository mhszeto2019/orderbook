import React, { useEffect, useState } from 'react';
import { io } from 'socket.io-client';

const SOCKET_URL = 'http://localhost:5000'; // Update with your server's WebSocket URL

const WebSocketClient = () => {
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const socket = io(SOCKET_URL);

    // Listen for connection event
    socket.on('connect', () => {
      console.log('Connected to WebSocket server');
    });

    // Listen for incoming messages
    socket.on('okx_orderbook', (data) => {
      console.log('Received data from OKX:', data);
      if (data && Object.keys(data).length > 0) {
        setMessages((prevMessages) => [...prevMessages, data]);
      } else {
        console.warn('Received empty data:', data);
      }
    });

    // Handle connection errors
    socket.on('connect_error', (err) => {
      console.error('Connection error with WebSocket:', err);
      setError(err);
    });

    // Handle disconnection
    socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket');
    });

    // Cleanup on component unmount
    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <div>
      <h1>WebSocket Client</h1>
      {error && <p style={{ color: 'red' }}>Error: {error.message}</p>}
      <h2>Received Messages:</h2>
      <ul>
        {messages.map((msg, index) => (
          <li key={index}>
            {JSON.stringify(msg)}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default WebSocketClient;
