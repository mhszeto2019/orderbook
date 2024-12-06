const socket = io('http://localhost:5001', {
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  timeout: 20000,
  transports: ['websocket']
});

let currentChannel = 'okx_fundingrate/BTC-USD-SWAP'; // Default channel
let activeListener = null;

function connectToChannel(channel) {
  if (activeListener) {
      console.log(`Removing listener for: ${activeListener}`);
      socket.off(activeListener);
  }

  activeListener = channel;

  console.log(`Subscribing to channel: ${channel}`);
  socket.on(channel, (message) => {
      try {
          const data = JSON.parse(message);
          console.log(`Message from ${channel}:`, data);

          const fundingRateElement = document.getElementById('fundingrate-okx');
          if (fundingRateElement) {
              const { funding_rate, ts, exchange } = data;
              const formattedTime = new Date(ts).toLocaleString();

              fundingRateElement.innerHTML = `
                OKX: ${exchange} - ${channel.split('/')[1]}<br>
                Funding Rate: ${funding_rate} <br>
                Last Updated: ${formattedTime}
              `;
              fundingRateElement.classList.replace('bg-danger', 'bg-success');
          }
      } catch (err) {
          console.error('Error parsing message:', err);
      }
  });
}

connectToChannel(currentChannel);

document.getElementById('currency-input').addEventListener('change', function () {
  const selectedCurrency = this.value;
  if (selectedCurrency) {
      currentChannel = `okx_fundingrate/${selectedCurrency}`;
      connectToChannel(currentChannel);
  }
});

socket.on('connect', () => {
  console.log('Connected to funding rate server');
});

socket.on('disconnect', () => {
  console.log('Disconnected from server');
  const fundingRateElement = document.getElementById('fundingrate-okx');
  if (fundingRateElement) {
      fundingRateElement.innerHTML = 'Disconnected';
      fundingRateElement.classList.replace('bg-success', 'bg-danger');
  }
});
