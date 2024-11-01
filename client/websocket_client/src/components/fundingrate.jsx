import React, { useEffect, useState } from 'react';
import { io } from 'socket.io-client';

const FundingRateTable = () => {
  const [fundingRates, setFundingRates] = useState([]);

  useEffect(() => {
    const fundingSocket = io("http://127.0.0.1:5001", {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    fundingSocket.on('connect', () => {
      console.log('Connected to funding rate socket');
    });

    // Listening for the funding rate event
    fundingSocket.on('okx_funding_rate', (fundingRateData) => {
      console.log('Funding rate data received:', fundingRateData);

      // Access the data from the wrapped object
      const { exchange, ccy, funding_rate, fundingTime, ts } = fundingRateData.data;

      // Create a new funding rate object
      const newFundingRate = {
        exchange: exchange || 'N/A',
        ccy: ccy || 'N/A',
        fundingRate: funding_rate || 'N/A', // Use the correct key for funding rate
        fundingTime, // Should be a timestamp in ms
        timestamp: ts, // Should be a timestamp in ms
      };

      // Update state: replace or add new funding rate
      setFundingRates((prevRates) => {
        // Check if the funding rate for this exchange and currency already exists
        const existingRateIndex = prevRates.findIndex(
          (rate) => rate.exchange === newFundingRate.exchange && rate.ccy === newFundingRate.ccy
        );

        if (existingRateIndex !== -1) {
          // If it exists, update the existing rate
          const updatedRates = [...prevRates];
          updatedRates[existingRateIndex] = newFundingRate; // Replace with the new funding rate
          return updatedRates;
        } else {
          // If it doesn't exist, add the new funding rate
          return [...prevRates, newFundingRate];
        }
      });
    });

    fundingSocket.on('disconnect', () => {
      console.log('Disconnected from funding rate socket');
    });

    return () => {
      fundingSocket.disconnect();
    };
  }, []);


  return (
    <div>
      <h2>Funding Rates</h2>
      <table border="1" cellPadding="10" cellSpacing="0">
        <thead>
          <tr>
            <th>Exchange</th>
            <th>Currency</th>
            <th>Funding Rate</th>
            <th>Funding Time</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {fundingRates.map((rate, index) => (
            <tr key={index}>
              <td>{rate.exchange}</td>
              <td>{rate.ccy}</td>
              <td>{rate.fundingRate}</td>
              <td>{rate.fundingTime}</td>
              <td>{rate.timestamp}</td> {/* Format timestamp here */}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default FundingRateTable;
