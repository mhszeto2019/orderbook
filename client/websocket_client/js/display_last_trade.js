// Connect to the Flask-SocketIO server
const htxsocketLastTrades = io('http://localhost:5099');
// const okxsocketLastTrades = io('http://localhost:5098');

// Maximum rows to store for each currency

// let lastTrades = {
//     "HTX":{"BTC_USD":{"SWAP":[{"price":10,"time":'xxxx',"direction":'buy'}]}},
// };

let lastTrades = {
    "HTX": {}, // Exchange
    "OKX": {}  // Another exchange
};

// Function to initialize the structure for a new currency pair
function initializeCurrencyPair(exchange, currencyPair, instrument) {
    if (!lastTrades[exchange][currencyPair]) {
        lastTrades[exchange][currencyPair] = {
            "SWAP": [],
            "SPOT": []
        };
    }
}

// Function to update the last trades
function updateLastTrades(exchange, currencyPair, message) {
    let instrument = message['instrument']
    console.log(message['tick'])
    initializeCurrencyPair(exchange, currencyPair, instrument);

    message.tick.data.forEach(row=>{
        newTrade = { "price": row['price'], "time": row['ts'], "direction": row['direction'], "amount":row['amount'] }
        // Maintain only the last 10 trades
        
        let tradesList = lastTrades[exchange][currencyPair][instrument];
        tradesList.unshift(newTrade); // Add new trade at the beginning
        
        if (tradesList.length > 10) {
            tradesList.pop(); // Remove oldest trade if more than 10 trades
        }
    })

    console.log(tradesList)
    
}

// // Example usage:
// updateLastTrades('HTX', 'BTC-USD', 'SWAP', { "price": 97635.5, "time": new Date().toISOString(), "direction": "buy" });
// updateLastTrades('OKX', 'ETH-USD', 'SPOT', { "price": 97500.0, "time": new Date().toISOString(), "direction": "sell" });




// Event: Connection established
htxsocketLastTrades.on('connect', () => {
    console.log('Connected to the WebSocket server');
    
    // Optionally, emit a test message to the server
    htxsocketLastTrades.emit('message', { msg: 'Hello from the client!' });
});

// Event: Handle incoming messages
htxsocketLastTrades.on('htx_trade_history', (data) => {
    console.log(data)
    
    updateLastTrades(data['exchange'],data['ccy'], data);
    // 'SWAP', { "price": 97635.5, "time": new Date().toISOString(), "direction": "buy" }
    console.log(lastTrades)



});

// Custom event handler (if the server emits specific events like 'BTC-USD-SWAP')
htxsocketLastTrades.on('BTC-USD-SWAP', (data) => {
    console.log('BTC-USD-SWAP event received:', data);
});

// Event: Handle server disconnect
htxsocketLastTrades.on('disconnect', () => {
    console.log('Disconnected from the WebSocket server');
});


// function handleLastTradeWebsocketMessage(message) {
//     // Parse the message
//     const channel = message.ch; // e.g., 'market.BTC-USD.trade.detail'
//     const tickData = message.tick.data; // Array of trade data

//     // Extract currency and instrument
//     const parts = channel.split('.');
//     const currency = parts[1]; // e.g., 'BTC-USD'
//     const instrument = parts[2] === 'trade' ? 'SWAP' : 'SPOT'; // Example logic

//     // Initialize the structure if not already present
//     if (!lastTrades[currency]) {
//         lastTrades[currency] = {};
//     }
//     if (!lastTrades[currency][instrument]) {
//         lastTrades[currency][instrument] = [];
//     }
//     console.log(lastTrades)
//     // Process each trade
//     tickData.forEach(trade => {
//         const tradeDetails = {
//             price: trade.price,
//             quantity: trade.quantity,
//             direction: trade.direction,
//             timestamp: new Date(trade.ts).toLocaleString()
//         };

//         // Add the trade to the front of the list
//         lastTrades[currency][instrument].unshift(tradeDetails);

//         // Keep only the last 10 trades
//         if (lastTrades[currency][instrument].length > MAX_TRADES) {
//             lastTrades[currency][instrument].pop();
//         }
//     });
//     console.log(lastTrades)
//     // Example: Populate the table (frontend logic)
//     const { selectedCurrency, selectedInstrument } = getSelectedOptions(); // Your logic

//     if (selectedCurrency === currency && selectedInstrument === instrument) {
//         populateTable(lastTrades[currency][instrument]);
//     }
// }

// function populateLastTrades(exchange,currency, data) {
//     // Loop through each table (orderbook 1 and orderbook 2)
//     console.log(exchange,data)
//     for (let i = 1; i <= 2; i++) {
//         // const timestamp = document.getElementById(`last-timestamp-${i}`);
//         // Get the selected exchange for the current table
//         const selectedExchange = document.getElementById(`selected-exchange-lastprice-${i}`).innerText;
//         const selectedCcyInstrument = document.getElementById(`selected-ccy-lastprice-${i}`).innerText;
//         let instrument = ''
//         let selectedCcy = ''
//         if (selectedCcyInstrument.endsWith('-SWAP')) {
//             instrument = 'SWAP';
//             selectedCcy = selectedCcyInstrument.replace('-SWAP', '');
//         }

//         if (selectedExchange === exchange && selectedCcy == currency) {
//             const tableBody = document.getElementById(`lastprice-data-table-body-${i}`);
//             console.log(selectedExchange,selectedCcy)
//             console.log(lastTrades[selectedCcy][selectedExchange])
//         }


//     }
// }


// function onLastTradeWsDataReceived(exchange,currency,message) {
//     try {
//         console.log(exchange,currency,message)
//         populateLastTrades(exchange,currency,message)
    
//     } catch (error) {
//         console.error("Error processing WebSocket data:", error);
//     }
// }
