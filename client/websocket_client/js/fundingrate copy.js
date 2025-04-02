  // const socket = io('http://localhost:5001', {
  //   reconnection: true,  // Enable reconnection
  //   reconnectionAttempts: 5, // Number of attempts before giving up
  //   reconnectionDelay: 1000, // Delay between reconnection attempts in ms
  //   reconnectionDelayMax: 5000, // Maximum delay for reconnection in ms
  //   timeout: 20000 ,// Timeout before connection attempt is considered failed,
  //   transports: ['websocket']
  // });

  // let currentCurrency = "BTC-USD-SWAP"; // Default selected currency
  // let activeListener = null; // Track the active listener

  // function connectToCurrency(currency) {
  //   if (activeListener) {
  //     // Remove the previous listener
  //     socket.off(activeListener);
  //   }

  //   const eventName = `${currency}`;
  //   activeListener = eventName; // Update the active listener

  //   console.log(`Listening to event: ${eventName}`);

  //   // Set up a listener for the selected currency
  //   socket.on(eventName, (data) => {
  //     console.log(`Received update for ${currency}:`, data);
  //     const fundingData = JSON.parse(data.data); // Parse the received JSON data

  //     // Update the funding rate and funding time display
  //     const fundingRateElement = document.getElementById('fundingrate-okx');
  //     if (fundingRateElement) {
  //       const fundingRate = fundingData.funding_rate;
  //       const fundingTime = fundingData.ts; // Timestamp when the funding rate was updated

  //       // Format the timestamp to a readable date
  //       const formattedTime = new Date(fundingTime).toLocaleString();

  //       // Update the content of the funding rate element
  //       fundingRateElement.innerHTML = `
  //         OKX: ${fundingData.exchange} - ${currency}<br>
  //         Funding Rate: ${fundingRate} <br>
  //         Last Updated: ${formattedTime}
  //       `;
  //       fundingRateElement.classList.replace('bg-danger', 'bg-success');
  //     }
  //   });
  // }

  // // Initialize the listener for the default currency
  // connectToCurrency(currentCurrency);

  // // Event handler for currency dropdown changes
  // document.getElementById('currency-input').addEventListener('change', function () {
  //   const selectedCurrency = this.value;
  //   if (selectedCurrency) {
  //     currentCurrency = selectedCurrency;
  //     connectToCurrency(currentCurrency);
  //   }
  // });

  // socket.on('connect',()=>{
  //   console.log('Connected to okx Funding rate server ')
  // })
  // // Handle disconnection
  // socket.on('disconnect', () => {
  //   console.log('Disconnected from server');
  //   const fundingRateElement = document.getElementById('fundingrate-okx');
  //   if (fundingRateElement) {
  //     fundingRateElement.innerHTML = `Disconnected`;
  //     fundingRateElement.classList.replace('bg-success', 'bg-danger');
  //   }
  // });

  // // Handle successful reconnection
  // socket.on('reconnect', () => {
  //   console.log('Reconnected to the server');
  //   const fundingRateElement = document.getElementById('fundingrate-okx');
  //   if (fundingRateElement) {
  //     fundingRateElement.innerHTML = `Reconnected`;
  //     fundingRateElement.classList.replace('bg-danger', 'bg-success');
  //   }
  // });

  // // Handle failed reconnection attempts
  // socket.on('reconnect_error', () => {
  //   console.log('Reconnection failed');
  //   const fundingRateElement = document.getElementById('fundingrate-okx');
  //   if (fundingRateElement) {
  //     fundingRateElement.innerHTML = `Reconnection Failed`;
  //     fundingRateElement.classList.replace('bg-success', 'bg-warning');
  //   }
  // });
