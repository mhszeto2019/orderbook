// Connect to the Flask-SocketIO server
const htxsocketLastTrades = io('http://localhost:5099');
// const okxsocketLastTrades = io('http://localhost:5098');

let lastTrades = {
    "HTX": {}, // Exchange
    "OKX": {}  // Another exchange
};

// Function to initialize the structure for a new currency pair
function initializeCurrencyPair(exchange, instrument,currencyPair) {
    // Ensure the exchange exists
    if (!lastTrades[exchange]) {
        lastTrades[exchange] = {};
    }

    // Ensure the instrument exists
    if (!lastTrades[exchange][instrument]) {
        lastTrades[exchange][instrument] = {}
    }
     // Ensure the currency pair exists
     if (!lastTrades[exchange][instrument][currencyPair]) {
        lastTrades[exchange][instrument][currencyPair] = []
    }
}

// Function to update the last trades
function updateLastTrades(exchange, currencyPair, message) {
    let instrument = message['instrument']
    console.log(message['tick'])
    initializeCurrencyPair(exchange,instrument,currencyPair);
    let tradesList = lastTrades[exchange][instrument][currencyPair];
    message.tick.data.slice().reverse().forEach(row=>{
        newTrade = { "price": row['price'], "time": row['ts'], "direction": row['direction'], "amount":row['amount'] }
        // Maintain only the last 10 trades
        tradesList.unshift(newTrade); // Add new trade at the beginning
        
        if (tradesList.length > 10) {
            tradesList.pop(); // Remove oldest trade if more than 10 trades
        }

    })
    
}




// Event: Connection established
htxsocketLastTrades.on('connect', () => {
    console.log('Connected to the WebSocket server');
    
    // Optionally, emit a test message to the server
    htxsocketLastTrades.emit('message', { msg: 'Hello from the client!' });
});

// Event: Handle incoming messages
htxsocketLastTrades.on('htx_trade_history', (data) => {
    updateLastTrades(data['exchange'],data['ccy'],data);
    onLastTradeWsDataReceived(data['exchange'],data['ccy'], data['instrument'])
});

// Custom event handler (if the server emits specific events like 'BTC-USD-SWAP')
htxsocketLastTrades.on('BTC-USD-SWAP', (data) => {
    console.log('BTC-USD-SWAP event received:', data);

});

// Event: Handle server disconnect
htxsocketLastTrades.on('disconnect', () => {
    console.log('Disconnected from the WebSocket server');
});


function onLastTradeWsDataReceived(exchange,currency,instrument) {
    try {
        populateLastTrades(exchange,currency,instrument)
    
    } catch (error) {
        console.error("Error processing WebSocket data:", error);
    }
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString(); // Format to local time
}


function populateLastTrades(exchange,currency,instrument) {
    // Loop through each table (orderbook 1 and orderbook 2)
    for (let i = 1; i <= 2; i++) {
        // const timestamp = document.getElementById(`last-timestamp-${i}`);
        // Get the selected exchange for the current table
        const selectedExchange = document.getElementById(`selected-exchange-lastprice-${i}`).innerText.toUpperCase();
        const selectedCcy= document.getElementById(`selected-ccy-lastprice-${i}`).innerText;

        // Check if the value ends with '-SWAP' and remove it if true
        const processedSelectedCcy = selectedCcy.endsWith('-SWAP') ? selectedCcy.replace('-SWAP', '') : selectedCcy;
        data = lastTrades[exchange][instrument][currency]
        
        
        
        if (selectedExchange == exchange && processedSelectedCcy == currency) {
            const tableBody = document.getElementById(`lastprice-data-table-body-${i}`);
            console.log(selectedExchange,processedSelectedCcy,'swap')
            // console.log(lastTrades[selectedExchange][selectedCcy][instrument])
            console.log(selectedExchange,exchange,instrument,processedSelectedCcy,currency,data)
            // Format the timestamp to a human-readable date
            

            // Populate table with new data
            data.forEach(trade => {
                const row = document.createElement('tr'); // Create a new table row

                // Create and append cells for price, time, direction, and amount
                row.innerHTML = `
                    <td>${formatTime(trade.time)}</td>
                    <td>${trade.price}</td>
                    <td>${trade.direction}</td>
                    <td>${trade.amount}</td>
                `;

                // Append the row to the table body
                tableBody.appendChild(row);
            });

        }


    }
}


