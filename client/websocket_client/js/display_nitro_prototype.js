function generateOrderbookHTML(exchange, orderbook) {
    // console.log(orderbook.ask_list,typeof JSON.parse(orderbook.ask_list))
     // Save the current scroll position
    
    if (!orderbook || !orderbook.ask_list || !orderbook.bid_list) {
        return `<div>No data available for ${exchange}</div>`;
    }
    return `
        <div>
            <h6>${exchange} Orderbook</h6>
            <div class="scrollable-orderbook">
                <div class="orderbook-timestamp">
                    Ts: <span id="${exchange}-timestamp">${orderbook.timestamp}</span>
                </div>
                <div class='asks'>
                    <ul>
                        ${(JSON.parse(orderbook.ask_list))
                            .map((entry) => `<li>${entry.price} (${entry.size})</li>`)
                            .join("")}
                    </ul>
                </div>
                <div>
                    <ul>
                        <li>
                            <p><strong>Current ASK / SIZE</strong></p>
                        </li>
                    </ul>
                </div>
                <div class='bids'>
                    <ul>
                        ${JSON.parse(orderbook.bid_list)
                            .map((entry) => `<li>${entry.price} (${entry.size})</li>`)
                            .join("")}
                    </ul>
                </div>
            </div>
        </div>
    `;
}

function populateOrderbookTable(orderbooks,data) {
    console.log('orderbooks',orderbooks,data)
    
    const tableMapping = {
        "okx-htx": ["okx", "htx"],
        "okx-bnb": ["okx", "bnb"],
        "htx-okx": ["htx", "okx"],
        "htx-bnb": ["htx", "bnb"],
        "bnb-okx": ["bnb", "okx"],
        "bnb-htx": ["bnb", "htx"],
    };

    // Loop through table mapping to dynamically update cells when data is available
    for (const [cellId, exchanges] of Object.entries(tableMapping)) {
        const [firstExchange, secondExchange] = exchanges;
        const cell = document.getElementById(cellId);

        // Check if data exists for both exchanges and update the cell dynamically
        const firstExchangeData = orderbooks[firstExchange];
        const secondExchangeData = orderbooks[secondExchange];
        if (cell) {
            // Update the first exchange data
            if (firstExchangeData) {
                cell.innerHTML = `
                    <div class="orderbook-container">
                        ${generateOrderbookHTML(firstExchange, firstExchangeData)}
                        ${secondExchangeData ? generateOrderbookHTML(secondExchange, secondExchangeData) : ''}
                    </div>
                `;
            }
            // Update the second exchange data when it arrives
            if (secondExchangeData && !firstExchangeData) {
                cell.innerHTML = `
                    <div class="orderbook-container">
                        ${generateOrderbookHTML(secondExchange, secondExchangeData)}
                        ${firstExchangeData ? generateOrderbookHTML(firstExchange, firstExchangeData) : ''}
                    </div>
                `;
            }
        }
    }
}


let orderbooks ={};
// Simulate data arriving slowly

function formatTimestamp(timestamp) {
    const date = new Date(timestamp); // assuming timestamp is in milliseconds
    return date.toLocaleTimeString(); // Convert to human-readable time
}

function updateOrderbookTimestamp(exchange, timestamp) {
    const timestampElement = document.getElementById(`${exchange}-timestamp`);
    if (timestampElement) {
        timestampElement.textContent = formatTimestamp(timestamp);
    }
}

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


// WS CONNECTIONS

// Start the simulated WebSocket data stream
// simulateWebSocketData();
const wsURLs = {
    okx: "ws://localhost:8765",  // Example WebSocket URL for OKX
    // htx: "ws://localhost:8766",  // Example WebSocket URL for HTX
    // bnb: "ws://localhost:8767"   // Example WebSocket URL for BNB
};

const wsConnections = {};  // Object to hold WebSocket connections
const maxReconnectAttempts = 5; // Max reconnection attempts
const reconnectDelay = 2000;  // Reconnection delay in milliseconds

// Function to create WebSocket connection
function connectWebSocket(exchange, url, attempt = 1) {
    const ws = new WebSocket(url);

    ws.onopen = () => {
        console.log(`Connected to ${exchange} WebSocket server.`);
        updateStatus(exchange, true); 

    };

    ws.onmessage = (event) => {
        const orderData = JSON.parse(event.data);  // Parse incoming data
        // console.log(orderData);
        console.log(exchange)
        orderbooks[exchange] = orderData
        populateOrderbookTable(orderbooks, orderData);  // Update the orderbook UI

    };

    ws.onclose = () => {
        console.log(`${exchange} WebSocket connection closed.`);
        // If the connection is closed, attempt to reconnect
        if (attempt <= maxReconnectAttempts) {
            console.log(`Attempting to reconnect to ${exchange}... (Attempt #${attempt})`);
            setTimeout(() => connectWebSocket(exchange, url, attempt + 1), reconnectDelay * attempt); // Exponential backoff
        } else {
            console.log(`Max reconnection attempts reached for ${exchange}.`);
        }
    };

    ws.onerror = (error) => {
        console.error(`${exchange} WebSocket error:`, error);
    };

    wsConnections[exchange] = ws;
}

function connectAllWebSockets() {
    for (const [exchange, url] of Object.entries(wsURLs)) {
        connectWebSocket(exchange, url);
    }
}

connectAllWebSockets();