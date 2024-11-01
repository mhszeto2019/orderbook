// src/App.js
import React, { useState, useEffect } from "react";
import LivePrices from "./components/LivePrices";
import OrderBook from "./components/OrderBook";
import './App.css';


function App() {
  const [selectedExchange, setSelectedExchange] = useState(null);
  const [selectedCcy, setSelectedCcy] = useState(null);

  return (
    <div className="app">
      <h1>WebSocket Price Updates</h1>
      <div className="flex-container">
        <LivePrices setSelectedExchange={setSelectedExchange} setSelectedCcy={setSelectedCcy} />
        <OrderBook selectedExchange={selectedExchange} selectedCcy={selectedCcy} />
      </div>
    </div>
  );
}

export default App;
