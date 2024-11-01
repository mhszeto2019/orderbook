// src/components/OrderBook.js
import React, { useEffect, useState } from "react";
import io from "socket.io-client";

const OrderBook = ({ selectedExchange, selectedCcy }) => {
  const [orderData, setOrderData] = useState({ bids: [], asks: [] });
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    if (!selectedExchange || !selectedCcy) return;

    const socketUrl = selectedExchange === "OKX" ? 'http://localhost:5000' : 'http://localhost:5010';
    const socket = io(socketUrl);
    setSocket(socket);

    socket.on('connect', () => {
      console.log(`Connected to ${selectedExchange} order book WebSocket`);
    });

    // Handler for order book updates
    const handleOrderBookData = (data) => {
      const { bids, asks } = JSON.parse(data);
      setOrderData({ bids, asks });
    };

    socket.on('order_book', handleOrderBookData);

    return () => {
      socket.disconnect();
    };
  }, [selectedExchange, selectedCcy]);

  return (
    <div className="orderbook-section">
      <h2>Order Book</h2>
      {selectedExchange && selectedCcy ? (
        <>
          <div id="selected-info">
            <p>Exchange: <span id="selected-exchange">{selectedExchange}</span></p>
            <p>Currency: <span id="selected-ccy">{selectedCcy}</span></p>
          </div>
          <div className="orderbook-scroll-container">
            <table className="orderBookTable">
              <thead>
                <tr>
                  <th>Price</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
                <tr><th colSpan="2">Bids</th></tr>
                {orderData.bids.map(([price, size], index) => (
                  <tr key={`bid-${index}`}>
                    <td>{price}</td>
                    <td>{size}</td>
                  </tr>
                ))}
                <tr><th colSpan="2">Asks</th></tr>
                {orderData.asks.map(([price, size], index) => (
                  <tr key={`ask-${index}`}>
                    <td>{price}</td>
                    <td>{size}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <p>Select a currency pair from Live Prices</p>
      )}
    </div>
  );
};

export default OrderBook;
