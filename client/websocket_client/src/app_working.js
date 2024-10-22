import React, { useEffect, useState } from 'react';
import io from 'socket.io-client';
import Ladderbook from './components/ladderbook';
import LivePricesDataRetriever from './components/liveprices';
import FundingRateTable from './components/fundingrate';
import './App.css';

// Socket server URLs
const OKX_SOCKET_SERVER_URL_ORDERBOOK = 'http://127.0.0.1:5000';
const SOCKET_SERVER_URL_FUNDINGRATE = 'http://127.0.0.1:5001';
const SOCKET_SERVER_URL_SPOTPRICE = 'http://127.0.0.1:5002';

function App() {
  const [ccyOrderbooks, setOrderbooks] = useState({});
  const [ccyPrices, setPrices] = useState({});
  const [selectedOrderbook, setSelectedOrderbook] = useState(null);

  const handleSelectOrderbook = (orderbook) => {
    setSelectedOrderbook(orderbook);
  };

  useEffect(() => {
    const socketOrderbook = io(OKX_SOCKET_SERVER_URL_ORDERBOOK);
    const socketFundingRate = io(SOCKET_SERVER_URL_FUNDINGRATE);
    const socketSpotPrice = io(SOCKET_SERVER_URL_SPOTPRICE);

    socketOrderbook.on('exchange', (data) => {
      const instId = data.data.data[0].instId.toLowerCase().replaceAll('-', '_');
      const orderbookDetails = data.data.data[0];
      setOrderbooks((prevBooks) => ({
        ...prevBooks,
        [instId]: orderbookDetails,
      }));
    });

    socketSpotPrice.on('spotprice', (data) => {
      const instId = data.data.data[0].instId.toLowerCase().replaceAll('-', '_');
      const tradeDetails = data.data.data[0];
      setPrices((prevPrices) => ({
        ...prevPrices,
        [instId]: tradeDetails,
      }));
    });

    socketFundingRate.on('fundingrate', (data) => {
      // Handle funding rate data if needed
      console.log("Funding rate data received:", data);
    });

    return () => {
      socketOrderbook.disconnect();
      socketFundingRate.disconnect();
      socketSpotPrice.disconnect();
    };
  }, []);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Data Aggregator</h1>
      </header>

      <main className="main-content">
        <section className="live-rates-section">
          <div style={{ display: 'flex', gap: '20px' }}>
            <LivePricesDataRetriever prices={ccyPrices} />
            <FundingRateTable />
          </div>
        </section>

        <section className="orderbook-section">
          <Ladderbook orderbooks={ccyOrderbooks} selectedOrderbook={selectedOrderbook} onSelectOrderbook={handleSelectOrderbook} />
        </section>
      </main>

      <footer className="app-footer">
        <h1>Order System</h1>
      </footer>
    </div>
  );
}

export default App;
