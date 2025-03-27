// // WebSocket URLs for each exchange (including paths for each exchange)
// const wsServers = {
//     'okx': 'ws://localhost:8765/okx',  // WebSocket for OKX
//     // 'okx':'http://127.0.0.1:5090',
//     'htx': 'ws://localhost:8765/htx',  // WebSocket for HTX
//     // 'bnb': 'ws://localhost:8765/bnb'   // WebSocket for Binance (example)
// };

// Store the WebSocket connections
const wsConnections = {};

// Store the exchange data for each exchange
const lastData = {
    'okx': null,
    'htx': null,
    'bnb': null
};

function updateStatus(exchange, isLive) {
    const badge = document.getElementById(`status-${exchange}`);
    if (badge) {
        if (isLive) {
            badge.classList.remove('bg-danger');
            badge.classList.add('bg-success');
            badge.innerText = `${exchange}: live`;
        } else {
            badge.classList.remove('bg-success');
            badge.classList.add('bg-danger');
            badge.innerText = `${exchange}: dead`;
        }
    }
}

function updateArbOrder(buySpreadpx,buysz,sellSpreadpx,sellsz,buysellgap){
    buySpreadDOM = document.getElementById('buySpread')
    sellSpreadDOM = document.getElementById('sellSpread')
    buySpreadSzDOM = document.getElementById('buySpreadSz')
    sellSpreadSzDOM = document.getElementById('sellSpreadSz')
    buysellgapDOM = document.getElementById('buysellgapPx')

    buySpreadDOM.innerHTML = buySpreadpx
    sellSpreadDOM.innerHTML = sellSpreadpx
    buySpreadSzDOM.innerHTML = buysz
    sellSpreadSzDOM.innerHTML = sellsz
    buysellgapDOM.innerHTML = buysellgap


}

function compareData(newData) {
    const exchange = newData.exchange;
    // const otherExchange = exchange === 'htx' ? 'okx' : 'htx';
    exchange1 = document.getElementById('exchange1-input').value
    exchange2 = document.getElementById('exchange2-input').value
    // Get the previous data for the current exchange and the other exchange
    const currentData = newData;
    const previousDataEx1 = lastData[exchange1];
    const previousDataEx2 = lastData[exchange2];
    // console.log("ex1:",previousDataEx1,"ex2:",previousDataEx2,"newdata",newData)
    // console.log(JSON.parse(currentData.bid_list)[0].price)
    // If both previous data exist, compare them
    if (previousDataEx1 && previousDataEx2) {
        // Get the best bid and ask prices for both exchanges
        const bestBidEx1 = JSON.parse(previousDataEx1.bid_price)
        const bestBidSzEx1 = JSON.parse(previousDataEx1.bid_size)
        const bestAskEx1 = JSON.parse(previousDataEx1.ask_price)
        const bestAskSzEx1 = JSON.parse(previousDataEx1.ask_size)

        const bestBidEx2 = JSON.parse(previousDataEx2.bid_price)
        const bestBidSzEx2 = JSON.parse(previousDataEx2.bid_size)
        const bestAskEx2 = JSON.parse(previousDataEx2.ask_price)
        const bestAskSzEx2 = JSON.parse(previousDataEx2.ask_size)
        
  
        
        // if user wants to buy, it will be buying from exchange1 and selling exchange2 so we take exchange2's bid - exchange1's ask
        // buySpread = Number(bestBidEx2.toFixed(2)) - Number(bestAskEx1.toFixed(2))
        buySpread = Math.round((bestBidEx2 - bestAskEx1) * 100)/100
        // buySzSpread = Math.round((bestBidSzEx2 - bestAskSzEx1) * 100)/100
        // console.log(bestBidSzEx2,bestAskSzEx1)

        buySzSpread = Math.min(bestBidSzEx2,bestAskSzEx1)


        sellSpread = Math.round((bestBidEx1 - bestAskEx2) * 100)/100
        // sellSzSpread = Math.round((bestBidSzEx1 - bestAskSzEx2) * 100)/100
        sellSzSpread = Math.min(bestBidSzEx1,bestAskSzEx2) 


        buysellgap = Math.round((buySpread - sellSpread) * 100)/100
        
        // console.log(bestBidEx2,bestAskEx1, bestBidEx1,bestAskEx2)
        // console.log("buySpread",buySpread, `(${buySzSpread})` ,"\nsellSpread",sellSpread,`(${sellSpread})`)

        updateArbOrder(buySpread,buySzSpread,sellSpread,sellSzSpread,buysellgap)
        
   
    }
  
    // Update the last data received for the current exchange
    lastData[exchange] = currentData;
  }
  
  // Function to process data when received (this can be customized)
  function onWsDataReceived(exchange, data) {
    // Custom logic to process the received data
    console.log(`Data received from ${exchange}:`, data);
  }


const wsServers = {
   
    'okx':`http://${hostname}:5090`,
    'htx':`http://${hostname}:5091`,


// 
};

// Function to connect to Socket.IO servers for all exchanges
function connectToSocketIO() {
    console.log("CONNECTING")
    Object.keys(wsServers).forEach(exchange => {
        const socketUrl = wsServers[exchange];
        
        // console.log(socketUrl)
        // Create a Socket.IO connection for the exchange
        const socket = io(socketUrl, {
            transports: ['websocket'],
            reconnection: true,               // Enable reconnection (default: true)
            reconnectionAttempts: 10,         // Number of attempts before giving up (default: Infinity)
            reconnectionDelay: 1000,          // Initial delay between attempts (default: 1000 ms)
            reconnectionDelayMax: 5000,       // Maximum delay between attempts (default: 5000 ms)
            timeout: 20000   
            // debug: false // Disable debug logging
        });  // Connect to the server
        
        // Listen for reconnection
        socket.on("reconnect", (attemptNumber) => {
            console.log(`Reconnected after ${attemptNumber} attempts`);
        });

        // Listen for reconnection attempts
        socket.on("reconnect_attempt", (attemptNumber) => {
            console.log(`Reconnection attempt ${attemptNumber}`);
        });

        // Listen for reconnection errors
        socket.on("reconnect_error", (error) => {
            console.error("Reconnection error:", error);
        });

        // Listen for reconnection failure
        socket.on("reconnect_failed", () => {
            console.error("Reconnection failed after all attempts");
        });

        // Handle Socket.IO connect event
        socket.on('connect', () => {
            console.log(`Connected to ${exchange} Socket.IO server at ${socketUrl}`);
            updateStatus(exchange, true);
        });

        // Handle Socket.IO connection error event
        socket.on('connect_error', (error) => {
            console.error(`Error occurred with ${exchange} Socket.IO connection:`, error);
        });

        // Handle Socket.IO disconnect event
        socket.on('disconnect', () => {
            console.log(`Disconnected from ${exchange} Socket.IO server.`);
            updateStatus(exchange, false);
        });

        // Handle incoming messages (use your custom event names for messages)
        // find out which currency first then we connect to that ws key
        // console.log(document.getElementById('currency-input').value )
        
        socket.on(document.getElementById('currency-input').value, (data) => {
            try {
                // console.log('data')
                // console.log(`Received data from ${exchange}:`, data);
                lastData[exchange] = data; // Store data for this exchange
                if (data.currency == document.getElementById('currency-input').value){
                    // console.log(data)
                    // console.log(data.currency)
                    compareData(data);
                    onWsDataReceived(exchange, data); // Handle the received data
                }
                
            } catch (error) {
                console.error(`Error processing data from ${exchange}:`, error);
            }
        });

        // Store the Socket.IO connection
        wsConnections[exchange] = socket;
    });
}

// Function to clear old data from lastData (for memory management)
function clearOldData() {
    Object.keys(lastData).forEach(exchange => {
        if (lastData[exchange] && Date.now() - lastData[exchange].timestamp > 60000) { // 1 minute timeout for data
            lastData[exchange] = null; // Clear data if it's older than 1 minute
            console.log(`Cleared old data for ${exchange}`);
        }
    });
}
// Periodically clear old data to manage memory
setInterval(clearOldData, 60000); // Clear old data every 60 seconds

connectToSocketIO()