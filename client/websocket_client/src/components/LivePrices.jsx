// src/components/LivePrices.js
import React, { useEffect, useState } from "react";
import io from "socket.io-client";

const LivePrices = ({ setSelectedExchange, setSelectedCcy }) => {
  const [liveData, setLiveData] = useState({});
  const [socket, setSocket] = useState(null);

  const fixedOrder = [
    { exchange: 'OKX', ccy: 'btcusdt' },
    { exchange: 'htx', ccy: 'btcusdt' },
    { exchange: 'OKX', ccy: 'btcusdc' },
    { exchange: 'htx', ccy: 'btcusdc' },
    { exchange: 'OKX', ccy: 'btcusdtswap' },
    { exchange: 'htx', ccy: 'btcusdtswap' },
    { exchange: 'OKX', ccy: 'btcusdcswap' },
    { exchange: 'htx', ccy: 'btcusdcswap' },
    { exchange: 'OKX', ccy: 'coin-m' },
    { exchange: 'htx', ccy: 'coin-m' },
  ];

  // Establish WebSocket connection and manage socket state
  useEffect(() => {
    const socket = io('http://localhost:5002', {
      transports: ['websocket'],
      withCredentials: true, // to support credentials if needed
    });

    setSocket(socket);

    socket.on('connect', () => {
      console.log('Connected to WebSocket with ID:', socket.id);
    });

    socket.on('disconnect', (reason) => {
      console.log('Disconnected from WebSocket:', reason);
    });

    // Cleanup WebSocket on unmount
    return () => {
      socket.disconnect();
    };
  }, []);

  // Handle live price updates from WebSocket
  useEffect(() => {
    if (!socket) return;

    const handlePriceUpdate = (data) => {
      const parsedData = JSON.parse(data);
      console.log("Received live data:", parsedData);

      const { exchange, ccy, lastPrice, lastSize, timestamp, channel } = parsedData;
      const key = `${exchange}_${ccy}`;

      setLiveData((prevData) => ({
        ...prevData,
        [key]: { exchange, ccy, lastPrice, lastSize, timestamp, channel }
      }));
    };

    socket.on('live_price', handlePriceUpdate);

    // Cleanup the event listener
    return () => {
      socket.off('live_price', handlePriceUpdate);
    };
  }, [socket]);

  // Handle selecting a row
  const handleSelect = (exchange, ccy) => {
    setSelectedExchange(exchange);
    setSelectedCcy(ccy);
  };

  // Sorting live data based on the fixedOrder
  const sortedData = fixedOrder.map((order) => {
    const key = `${order.exchange}_${order.ccy}`;
    return liveData[key];
  }).filter((data) => data !== undefined);

  return (
    <div className="live-prices-section">
      <h2>Live Prices</h2>
      <table className="livePricesTable">
        <thead>
          <tr>
            <th>Exchange</th>
            <th>CCY</th>
            <th>Last Price</th>
            <th>Size</th>
            <th>Timestamp</th>
            <th>Channel</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {sortedData.length === 0 ? (
            <tr><td colSpan="7">Loading data...</td></tr>
          ) : (
            sortedData.map((data, index) => (
              <tr key={index}>
                <td>{data.exchange}</td>
                <td>{data.ccy}</td>
                <td>{data.lastPrice || '-'}</td>
                <td>{data.lastSize || '-'}</td>
                <td>{data.timestamp || '-'}</td>
                <td>{data.channel || '-'}</td>
                <td>
                  <button onClick={() => handleSelect(data.exchange, data.ccy)}>
                    Select
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default LivePrices;
