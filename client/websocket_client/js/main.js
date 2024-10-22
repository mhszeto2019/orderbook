const sockets = {
    okx: io('http://localhost:5002', {
        transports: ['websocket'],
        // debug: false // Disable debug logging
    }),
    htx: io('http://localhost:5012', {
        transports: ['websocket'],
        // debug: false // Disable debug logging
    }),
    fundingRate: io('http://localhost:5001', {
        transports: ['websocket'],
        // debug: false // Disable debug logging
    }),
    okx_orderBook: io('http://localhost:5000', {
        transports: ['websocket'],
        // debug: false // Disable debug logging
    }),
    htx_orderBook: io('http://localhost:5010', {
        transports: ['websocket'],
        // debug: false // Disable debug logging
    })

};


let historicalMap = {};
let activeOrderBookSocket = null;
const currencyMap = {};

const fixedOrder = [
    { exchange: 'OKX', ccy: 'btcusdt' },
    { exchange: 'htx', ccy: 'btcusdt' },
    { exchange: 'OKX', ccy: 'btcusdc' },
    { exchange: 'htx', ccy: 'btcusdc' },
    { exchange: 'OKX', ccy: 'btcusdtswap' },
    // { exchange: 'htx', ccy: 'btcusdtswap' },
    { exchange: 'OKX', ccy: 'btcusdcswap' },
    // { exchange: 'htx', ccy: 'btcusdcswap' },
    { exchange: 'OKX', ccy: 'coin-m' },
    { exchange: 'htx', ccy: 'coin-m' },
];



// Optimize connection logging
Object.entries(sockets).forEach(([name, socket]) => {
    socket.on('connect', () => console.log(`Connected to ${name} WebSocket`));
});

// Unified handler for all price updates
sockets.okx.onAny((event, message) => handlePriceUpdate(event, message));
sockets.htx.onAny((event, message) => handlePriceUpdate(event, message));
sockets.fundingRate.onAny((event, message) => handleFundingRateUpdate(event, message));

// Function to update the selected exchange and currency in the UI
function updateSelectedExchangeAndCcy(exchange, ccy,tableNo) {
    const selectedExchangeElement = document.getElementById(`selected-exchange-${tableNo}`);
    const selectedCcyElement = document.getElementById(`selected-ccy-${tableNo}`);

    // Update the text content with the selected exchange and currency
    selectedExchangeElement.textContent = exchange ? exchange : "Not Selected";
    selectedCcyElement.textContent = ccy ? ccy : "Not Selected";
}



function handlePriceUpdate(event, message) {
    if (event.startsWith('okx_live_price_') || event.startsWith('htx_live_price_')) {
        try {
            const { exchange, ccy, bidPrice,askPrice,lastPrice, lastSize, ts, channel } = JSON.parse(message.data);

            updatePriceData(exchange, ccy,  lastPrice, lastSize, ts, channel , bidPrice,askPrice,);
        } catch (error) {
            console.error("Error parsing price update:", error);
        }
    }
}



function handleFundingRateUpdate(event, message) {
    try {
        // console.log(message)
        const { exchange, ccy, funding_rate, ts } = JSON.parse(message.data);
        updateFundingRate(exchange, ccy, funding_rate, ts);
    } catch (error) {
        console.error("Error parsing funding rate update:", error);
    }
}

// Function to fetch the funding rate from the API
async function fetchFundingRate() {
    try {
        
        const response = await fetch("http://localhost:5011/get_funding_rate?contract_code=BTC-USD");
        // console.log(response)

        const data = await response.json();
        // Call handleFundingRateUpdate with the API data
        handleFundingRateUpdate(null, { data: JSON.stringify(data) });
    } catch (error) {
        console.error("Error fetching funding rate:", error);
    }
}

// Fetch funding rate every 60 seconds (60000 ms)
setInterval(fetchFundingRate, 5000);


function updatePriceData(exchange, ccy, lastPrice, lastSize, timestamp, channel, bidPrice,askPrice,) {
    const key = `${exchange}_${ccy}`;
    currencyMap[key] = { exchange, ccy, lastPrice, lastSize, timestamp, channel, fundingRate: currencyMap[key]?.fundingRate || '-' , bidPrice,askPrice,};
    historicalMap[key] = { lastPrice, lastSize ,bidPrice,askPrice,};

    updateTable();
}

function updateFundingRate(exchange, ccy, fundingRate, fundingTime) {
    const key = `${exchange}_${ccy}`;
    if (currencyMap[key]) {
        currencyMap[key].fundingRate = fundingRate;
        currencyMap[key].fundingTime = fundingTime;
    }

    updateTable();
}




function updateTable() {
    const tableBody = document.getElementById('live-data-table-body');

    // Iterate over the fixed order and update the table rows
    fixedOrder.forEach(pair => {
        const key = `${pair.exchange}_${pair.ccy}`;
        const data = currencyMap[key] || {};

        // Check if the row for this pair already exists
        let row = document.getElementById(key);

        if (!row) {
            // Create the row if it doesn't exist
            row = document.createElement('tr');
            row.id = key;
            row.innerHTML = `
                <td>${pair.exchange}</td>
                <td>${pair.ccy}</td>
             
                <td class="lastPrice-lastSize">
                    <div class="lastPrice" data-key="lastPrice">-</div> <!-- Last Price -->
                    <div class="lastSize" data-key="lastSize">(-)</div> <!-- Last Size below last Price -->
                </td>
                <td class="bidPrice" data-key="bidPrice">${historicalMap[pair.exchange,'_',pair.ccy]}</td>
                <td class="askPrice" data-key="askPrice">-</td>
                
                <td class="fundingRate" data-key="fundingRate">-</td>
                <td class="timestamp" data-key="timestamp">-</td>
                <td>
                    <button onclick="populateOrderBook('${pair.exchange}', '${pair.ccy}', 1)">Select</button>
                    <button onclick="populateOrderBook('${pair.exchange}', '${pair.ccy}', 2)">Select</button>
                    <button onclick="buy('${pair.exchange}', '${pair.ccy}')">Buy</button> <!-- Buy Button -->
                    <button onclick="sell('${pair.exchange}', '${pair.ccy}')">Sell</button> <!-- Sell Button -->
                </td>
                

            `;
            tableBody.appendChild(row);
        }

        // Update only the price-related cells (preserve the Action column)
        row.querySelector('[data-key="lastPrice"]').innerText = data.lastPrice || '-';
        row.querySelector('[data-key="lastSize"]').innerText = `(${data.lastSize})` || '( - )';
        row.querySelector('[data-key="bidPrice"]').innerText = data.bidPrice || '-';
        row.querySelector('[data-key="askPrice"]').innerText = data.askPrice || '-';
        row.querySelector('[data-key="fundingRate"]').innerText = data.fundingRate || '-';
        
     
        row.querySelector('[data-key="timestamp"]').innerText = data.timestamp || '-';
        // row.querySelector('[data-key="channel"]').innerText = data.channel || '-';

    });
}



function populateOrderBook(exchange, ccy,tableNo) {
    // console.log(exchange,ccy)
    const selectedExchange = exchange; // Example: Replace with actual selection logic
    const selectedCcy = ccy; // Example: Replace with actual selection logic

    updateSelectedExchangeAndCcy(selectedExchange, selectedCcy,tableNo);
    const orderDataTableBody = document.getElementById(`order-data-table-body-${tableNo}`);
    orderDataTableBody.innerHTML = '';

    // Disconnect the previous WebSocket if it exists
    if (activeOrderBookSocket && activeOrderBookSocket.connected) {
        activeOrderBookSocket.disconnect();
        console.log('Disconnected from previous WebSocket');
    }

    // Connect to the new WebSocket based on the selected exchange
    if (exchange === 'OKX') {
        activeOrderBookSocket = sockets.okx_orderBook;
    } else if (exchange === 'htx') {
        activeOrderBookSocket = sockets.htx_orderBook;
    }

    // Reconnect to the new WebSocket
    if (activeOrderBookSocket) {
        activeOrderBookSocket.connect();
        console.log(`Connected to ${exchange} order book WebSocket for ${ccy}`);

        // Listen for the order book data from the new WebSocket
        activeOrderBookSocket.onAny((event, message) => handleOrderBookData(exchange, ccy, message,tableNo));
    }
}



// Data structure to store the last received order book data
const lastData = {};