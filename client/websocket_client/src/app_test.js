// src/App.js

import React, { useEffect, useState } from 'react';
import io from 'socket.io-client';
import axios from 'axios';
import CurrencyPriceTable from './components/pricefile'
import LadderOrderBook from './components/orderbook';
import SocketIoDataRetriever from './components/test';

const SOCKET_SERVER_URL_orderbook = 'http://127.0.0.1:5000'; 
const SOCKET_SERVER_URL_fundingrate = 'http://127.0.0.1:5001'; 
const SOCKET_SERVER_URL_spotprice = 'http://127.0.0.1:5002'; 



function App() {
  
  // live - okx
  const [orderbookData, setOrderbookData] = useState(null);
  const [ccyOrderbooks, setOrderbooks] = useState(null);


  const [fundingrateData, setFundingrateData] = useState(null);

  const [spotpriceData, setSpotPrice] = useState(null);
  const [ccyPrices, setPrices] = useState(null);


  // cached
  const [cachedOrderbook, setCachedOrderbook] = useState(null);
  const [cachedFundingrate, setCachedFundingrate] = useState(null);
  const [cachedSpotprice, setCachedSpotPrice] = useState(null);
  
  // live - htx
  const [htxspotpriceData, sethtxSpotPrice] = useState(null);

  useEffect(() => {
    // OKX
    // Initialize socket connection
    const socket_orderbook = io(SOCKET_SERVER_URL_orderbook);
    const socket_fundingrate = io(SOCKET_SERVER_URL_fundingrate);
    const socket_spotprice = io(SOCKET_SERVER_URL_spotprice);

    // Listen for data from orderbook server
    socket_orderbook.on('exchange_data', (data) => {
      var instId = data.data.data[0].instId.toLowerCase()
      var instId = instId.replaceAll('-','_')
      var orderbook_dets = data.data.data[0]
      // console.log(orderbook_dets)

      setOrderbooks((prevBooks) => ({
        ...prevBooks,
        [instId]: orderbook_dets, // Use instId as the key
      }));
      
      // setOrderbookData(data.data); 
    });

    // Listen for data from fundingrate server
    socket_fundingrate.on('fundingrate', (data) => {
      setFundingrateData(data.data); 
    });

    // Listen for data from fundingrate server
    socket_spotprice.on('spotprice', (data) => {
   
      var instId = data.data.data[0].instId.toLowerCase()
      var instId = instId.replaceAll('-','_')
      var trade_dets = data.data.data[0]
      // console.log("DATA",instId,trade_dets)
      setPrices((prevPrices) => ({
        ...prevPrices,
        [instId]: trade_dets, // Use instId as the key
      }));


      setSpotPrice(data.data); 
    });

    // Cleanup on unmount
    return () => {
      socket_orderbook.disconnect();
      socket_fundingrate.disconnect();
      socket_spotprice.disconnect();

    };

  }, []);

// Helper function to group data by 0.1 intervals
// For example, a price of 63000.01 through 63000.09 will all be placed into the 63000.0 interval.
// Similarly, a price from 63000.1 through 63000.19 will fall into 63000.1.
const groupByInterval = (data, interval = 0.1) => {
  const groupedData = {};


  data.forEach(([price, volume]) => {
    // Calculate the interval range
    const range = Math.floor(price / interval) * interval;
    const rangeKey = range.toFixed(1); // Ensure we keep 1 decimal place for the range

    // Sum volumes for the same range
    if (groupedData[rangeKey]) {
      groupedData[rangeKey] += volume;
    } else {
      groupedData[rangeKey] = volume;
    }
  });
  

  // Convert the grouped data back to an array, sorted by price
  return Object.entries(groupedData)
    .map(([price, volume]) => [parseFloat(price), volume])
    .sort((a, b) => a[0] - b[0]);
};


  const fetchCachedFundingRateData = async () => {
    try {
      // Promise all helpsd to run both fetch calls in parallel
      const [orderbookResponse, fundingrateResponse] = await Promise.all([
        fetch('http://localhost:5000/cached_orderbook'),
        fetch('http://localhost:5001/cached_fundingrate')
      ]);
      // wait for responses to be received and then parse the JSON responses
      const orderbookData = await orderbookResponse.json();
      // console.log("orderbook_data", orderbookData.data);
      setCachedOrderbook(orderbookData);

      const fundingrateData = await fundingrateResponse.json();
      // console.log("fundingrate_DATA", fundingrateData.data);
      setCachedFundingrate(fundingrateData);

      

    } catch (error) {
      console.error('Error fetching funding rate data:', error);
    }
  };


  useEffect(() => {

    fetchCachedFundingRateData();

  }, [ccyPrices]);

  return (
    <div>
      <h1>Data</h1>
      {/* Display real-time data */}
      
      <div className="flex-container">

        <div className="flex-item">
          <h2>Price</h2>
          {ccyPrices ? (
                      <div>
                      <CurrencyPriceTable ccyPrices={ccyPrices} cachedFundingrate={cachedFundingrate} />
                      </div>
                      
            ) : ccyPrices ? (
              
              <pre>{JSON.stringify(cachedSpotprice.data, null, 2)}</pre>
            ) : (
              <p>No spot price data available...</p>
            )} 

            
        </div>
        
        



          
        <div className="flex-item">
          <h2>Real-time Funding Rate</h2>
          {/* <div>
            <LadderOrderBook ccyOrderbooks={ccyOrderbooks} />
          </div> */}

          <div>
            <SocketIoDataRetriever />
          </div>
          
        
        </div>

      </div>


    </div>

  );
}

export default App;
