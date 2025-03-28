// Connect to the Flask-SocketIO server
const htxsocketLastTrades = io(`http://${hostname}:6101`);
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
function updateLastTrades(exchange, currencyPair,instrument, message) {
    initializeCurrencyPair(exchange,instrument,currencyPair);
    
    let tradesList = lastTrades[exchange][instrument][currencyPair];
    message.forEach(row=>{
        newTrade = { "px": row['px'], "ts": row['ts'], "side": row['side'], "sz":row['sz'] }
        // Maintain only the last 10 trades
        tradesList.unshift(newTrade); // Add new trade at the beginning
        
        if (tradesList.length > 10) {
            tradesList.pop(); // Remove oldest trade if more than 10 trades
        }

    })
    
}


async function getTradeHistory(){
    const token = getAuthToken();
    const username = localStorage.getItem('username');
    const redis_key = localStorage.getItem('key');


    if (!token || !username || !redis_key) {
        // alert("You must be logged in to access this.");
        return;
    }
    ccy = document.getElementById('currency-input').value

    const request_data = { "username": username, "redis_key": redis_key,'ccy':ccy };

    const firstLastTradePromise = fetch(`http://${hostname}:6100/okx/gettradehistory`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request_data)
    });


    const results = await Promise.allSettled([firstLastTradePromise]);

    // Handle OKX Response
    if (results[0].status === 'fulfilled') {
        const response = results[0].value;
        if (response.ok) {
            
            const response_data = await response.json();
            updateLastTrades(response_data['exchange'],response_data['ccy'],response_data['instrument'],response_data['data']);
            onLastTradeWsDataReceived(response_data['exchange'],response_data['ccy'], response_data['instrument'])
            
        } else {
            console.error('Error fetching OKX orders:', response.statusText);
        }
    } else {
        console.error('OKX Request failed:', results[0].reason);
    }

   
}

function unixTsConversionHoursMinutes(timestampString) {
    const timestamp = Number(timestampString);
    if (!timestamp || isNaN(timestamp)) {
        return "Invalid timestamp";
    }

    // Convert the timestamp to a Date object
    const date = new Date(timestamp);

    // Extract the components of the time
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    const seconds = String(date.getSeconds()).padStart(2, "0");
    const milliseconds = String(date.getMilliseconds()).padStart(3, "0");

    // Format as hh:mm:ss:ms
    return `${hours}:${minutes}:${seconds}:${milliseconds}`;
}





// Event: Connection established
htxsocketLastTrades.on('connect', () => {
    console.log('Connected to the WebSocket server');
    
    // Optionally, emit a test message to the server
    htxsocketLastTrades.emit('message', { msg: 'Hello from the client!' });
});

// Event: Handle incoming messages
htxsocketLastTrades.on('htx_trade_history', (data) => {
    formattedData = htx2okxLastTrade(data)
    updateLastTrades(data['exchange'],data['ccy'],data['instrument'],formattedData);
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


function htx2okxLastTrade(htxData){
    return htxData.tick.data.map(trade => ({
        exchange: htxData.exchange,
        instrument: htxData.instrument,
        currencyPair: htxData.ccy,
        px: trade.price,
        ts: trade.ts,
        side: trade.direction,
        sz: trade.amount
    }));
}

function onLastTradeWsDataReceived(exchange,currency,instrument) {
    try {
        populateLastTrades(exchange,currency,instrument)
    
    } catch (error) {
        console.error("Error processing WebSocket data:", error);
    }
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
            tableBody.innerHTML = ''
            // console.log(lastTrades[selectedExchange][selectedCcy][instrument])
            // Format the timestamp to a human-readable date
            

            // Populate table with new data
            data.forEach(trade => {
                const row = document.createElement('tr'); // Create a new table row

                // Create and append cells for price, time, direction, and amount
                // row.innerHTML = `
                //     <td>${trade.ts}</td>
                //     <td class ='${trade.direction}'>${trade.price}</td>
                //     <td class='${trade.direction}'>${trade.direction}(${trade.amount})</td>
                // `;
                row.innerHTML = `
                    <td>${unixTsConversionHoursMinutes(trade.ts)}</td>

                    <td class ='${trade.side}'>${Number(trade.px).toLocaleString()}</td>
                    <td class='${trade.side}'>${trade.sz}</td>
                `;

                // Append the row to the table body
                tableBody.appendChild(row);
            });

        }


    }
}


// // // Set up the scheduler
function startLastTradeScheduler(interval = 5000) {
    // Call getTradeHistory immediately
    getTradeHistory();

    // Schedule getTradeHistory to run every few seconds
    setInterval(getTradeHistory, interval);
}

// Start the scheduler when the page loads
document.addEventListener('DOMContentLoaded', () => {
    startLastTradeScheduler();
});
