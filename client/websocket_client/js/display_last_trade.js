// Connect to the Flask-SocketIO server
const htxsocketLastTrades = io('http://localhost:5099');
const okxsocketLastTrades = io('http://localhost:5098');

// Maximum rows to store for each currency
const MAX_TRADES = 10;

let lastTrades = {
    'BTC-USD': {
        SWAP: [], // Array for BTC-USD SWAP trades
        SPOT: []  // Array for BTC-USD SPOT trades
    },
    'ETH-USD': {
        SWAP: [],
        SPOT: []
    }
};

// Event: Connection established
htxsocketLastTrades.on('connect', () => {
    console.log('Connected to the WebSocket server');
    
    // Optionally, emit a test message to the server
    htxsocketLastTrades.emit('message', { msg: 'Hello from the client!' });
});

// Event: Handle incoming messages
htxsocketLastTrades.on('htx_trade_history', (data) => {
    handleWebSocketMessage(data)
    // console.log('Message from server:', data);


});

// Custom event handler (if the server emits specific events like 'BTC-USD-SWAP')
htxsocketLastTrades.on('BTC-USD-SWAP', (data) => {
    console.log('BTC-USD-SWAP event received:', data);
});

// Event: Handle server disconnect
htxsocketLastTrades.on('disconnect', () => {
    console.log('Disconnected from the WebSocket server');
});



// Event: Connection established
okxsocketLastTrades.on('connect', () => {
    console.log('Connected to the WebSocket server');
    
    // Optionally, emit a test message to the server
    okxsocketLastTrades.emit('message', { msg: 'Hello from the client!' });
});

// Event: Handle incoming messages
okxsocketLastTrades.on('okx_trade_history', (data) => {
    // console.log('Message from server:', data);
    // handleWebSocketMessage(data)
});

// Custom event handler (if the server emits specific events like 'BTC-USD-SWAP')
okxsocketLastTrades.on('BTC-USD-SWAP', (data) => {
    console.log('BTC-USD-SWAP event received:', data);
});

// Event: Handle server disconnect
okxsocketLastTrades.on('disconnect', () => {
    console.log('Disconnected from the WebSocket server');
});


function handleWebSocketMessage(message) {
    // Parse the message
    const channel = message.ch; // e.g., 'market.BTC-USD.trade.detail'
    const tickData = message.tick.data; // Array of trade data

    // Extract currency and instrument
    const parts = channel.split('.');
    const currency = parts[1]; // e.g., 'BTC-USD'
    const instrument = parts[2] === 'trade' ? 'SWAP' : 'SPOT'; // Example logic

    // Initialize the structure if not already present
    if (!lastTrades[currency]) {
        lastTrades[currency] = {};
    }
    if (!lastTrades[currency][instrument]) {
        lastTrades[currency][instrument] = [];
    }
    console.log(lastTrades)
    // Process each trade
    tickData.forEach(trade => {
        const tradeDetails = {
            price: trade.price,
            quantity: trade.quantity,
            direction: trade.direction,
            timestamp: new Date(trade.ts).toLocaleString()
        };

        // Add the trade to the front of the list
        lastTrades[currency][instrument].unshift(tradeDetails);

        // Keep only the last 10 trades
        if (lastTrades[currency][instrument].length > MAX_TRADES) {
            lastTrades[currency][instrument].pop();
        }
    });
    console.log(lastTrades)
    // Example: Populate the table (frontend logic)
    const { selectedCurrency, selectedInstrument } = getSelectedOptions(); // Your logic

    if (selectedCurrency === currency && selectedInstrument === instrument) {
        populateTable(lastTrades[currency][instrument]);
    }
}

function getSelectedOptions() {
    const currencySelect = document.getElementById('currencySelect');
    const currencySelect = document.getElementById('currencySelect');

    return currencySelect.value;
}

function onWsDataReceived(exchange,message) {
    try {
        
        populateOrderBook(exchange,message)
    
    } catch (error) {
        console.error("Error processing WebSocket data:", error);
    }
}

// Populate Table Function
function populateTable(trades, tableKey) {
    // Check if data is the same as last update
    if (JSON.stringify(lastDisplayedTrades[tableKey]) === JSON.stringify(trades)) {
        return; // Do not update if there's no new data
    }

    // Update the cache with the new trades
    lastDisplayedTrades[tableKey] = trades;

    // Get the table body by ID
    const tableBody = document.getElementById('lastprice-data-table-body-2');
    tableBody.innerHTML = ''; // Clear existing rows

    // Append new rows to the table
    trades.forEach(trade => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${trade.price}</td>
            <td>${trade.quantity}</td>
            <td>${trade.direction}</td>
            <td>${trade.timestamp}</td>
        `;
        tableBody.appendChild(row);
    });
}