import React, { useEffect } from 'react';
import { io } from 'socket.io-client';

const SOCKET_SERVERS = {
  okx: 'http://127.0.0.1:5000',
  htx: 'http://127.0.0.1:5010',
};

const TestConnection = () => {
  useEffect(() => {
    // Create WebSocket connections to OKX and HTX
    const okxSocket = io(SOCKET_SERVERS.okx);
    const htxSocket = io(SOCKET_SERVERS.htx);

    // Handle OKX WebSocket connection and data
    okxSocket.on('connect', () => {
      console.log('Connected to OKX WebSocket server');
    });

    okxSocket.on('okx_orderbook', (data) => {
      console.log('Received data from OKX:', data);
    });

    okxSocket.on('connect_error', (err) => {
      console.error('Connection error with OKX:', err);
    });

    // Handle HTX WebSocket connection and data
    htxSocket.on('connect', () => {
      console.log('Connected to HTX WebSocket server');
    });

    htxSocket.on('htx_orderbook', (data) => {
      console.log('Received data from HTX:', data);
    });

    htxSocket.on('connect_error', (err) => {
      console.error('Connection error with HTX:', err);
    });

    // Cleanup on component unmount
    return () => {
      okxSocket.disconnect();
      htxSocket.disconnect();
    };
  }, []);

  return (
    <div>
      <h1>Testing WebSocket Connection</h1>
      <p>Open the browser console to view the WebSocket connection status and data.</p>
    </div>
  );
};

export default TestConnection;
