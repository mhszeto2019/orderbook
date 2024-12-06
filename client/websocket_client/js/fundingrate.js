import { createClient } from 'redis';

const client = createClient();

client.on('error', err => console.log('Redis Client Error', err));

await client.connect();


let currentCurrency = "BTC-USD-SWAP"; // Default selected currency
let activeListener = null; // Track the active listener

// Function to connect to the selected currency's funding rate data
function connectToCurrency(currency) {
  if (activeListener) {
    // Remove the previous listener for the active currency
    socket.off(activeListener);
  }

  const eventName = `${currency}`;  // Create event name from currency symbol
  activeListener = eventName;  // Update active listener to current currency

  console.log(`Listening to event: ${eventName}`);

  // Set up a listener for the selected currency's funding rate updates
  socket.on(eventName, (data) => {
    console.log(`Received update for ${currency}:`, data);
    const fundingData = JSON.parse(data.data); // Parse the received JSON data

    // Update the funding rate and funding time display
    const fundingRateElement = document.getElementById('fundingrate-okx');
    if (fundingRateElement) {
      const fundingRate = fundingData.funding_rate;
      const fundingTime = fundingData.ts; // Timestamp when the funding rate was updated

      // Format the timestamp to a readable date
      const formattedTime = new Date(fundingTime).toLocaleString();

      // Update the content of the funding rate element
      fundingRateElement.innerHTML = `
        OKX: ${fundingData.exchange} - ${currency}<br>
        Funding Rate: ${fundingRate} <br>
        Last Updated: ${formattedTime}
      `;
      fundingRateElement.classList.replace('bg-danger', 'bg-success'); // Show success color on update
    }
  });
}

// Initialize the listener for the default currency
connectToCurrency(currentCurrency);

// Event handler for currency dropdown changes
document.getElementById('currency-input').addEventListener('change', function () {
  const selectedCurrency = this.value;
  if (selectedCurrency && selectedCurrency !== currentCurrency) {
    currentCurrency = selectedCurrency;
    connectToCurrency(currentCurrency);  // Reconnect to new currency's data
  }
});

// Connection handling
socket.on('connect', () => {
  console.log('Connected to OKX Funding Rate server');
  const fundingRateElement = document.getElementById('fundingrate-okx');
  if (fundingRateElement) {
    fundingRateElement.innerHTML = `Connected to OKX`;
    fundingRateElement.classList.replace('bg-danger', 'bg-success');
  }
});

// Handle disconnection
socket.on('disconnect', () => {
  console.log('Disconnected from server');
  const fundingRateElement = document.getElementById('fundingrate-okx');
  if (fundingRateElement) {
    fundingRateElement.innerHTML = `Disconnected`;
    fundingRateElement.classList.replace('bg-success', 'bg-danger');
  }
});

// Handle successful reconnection
socket.on('reconnect', () => {
  console.log('Reconnected to the server');
  const fundingRateElement = document.getElementById('fundingrate-okx');
  if (fundingRateElement) {
    fundingRateElement.innerHTML = `Reconnected`;
    fundingRateElement.classList.replace('bg-danger', 'bg-success');
  }
});

// Handle failed reconnection attempts
socket.on('reconnect_error', () => {
  console.log('Reconnection failed');
  const fundingRateElement = document.getElementById('fundingrate-okx');
  if (fundingRateElement) {
    fundingRateElement.innerHTML = `Reconnection Failed`;
    fundingRateElement.classList.replace('bg-success', 'bg-warning');
  }
});
