

// // Store the WebSocket connections
// const wsConnections = {};

// // Store the exchange data for each exchange
// let lastData = {
//     'okxperp': {},
//     'htxperp': {},
//     'binanceperp': {}
// };


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
    // const exchange = newData.exchange;
    // // const otherExchange = exchange === 'htx' ? 'okx' : 'htx';
    let exchange1 = document.getElementById('exchange1-input').value
    let exchange2 = document.getElementById('exchange2-input').value
    let marketType1 = document.getElementById('market-type-orderbook1').value
    let marketType2 = document.getElementById('market-type-orderbook2').value
    let ccy1 = document.getElementById('currency-input-orderbook1').value
    let ccy2 = document.getElementById('currency-input-orderbook2').value

    // // Get the previous data for the current exchange and the other exchange
    if (marketType1 == 'perp'){
        exchange1 = exchange1 + 'perp'
    }
    else{
        exchange1 = exchange1 + 'spot'

    }

    if (marketType2 == 'perp'){
        exchange2 = exchange2 + 'perp'
    }
    else{
        exchange2 = exchange2 + 'spot'

    }
    // console.log(exchange1,exchange2)
    // const currentData = newData;
    const previousDataEx1 = lastData[exchange1];
    const previousDataEx2 = lastData[exchange2];
    // if (previousDataEx1[ccy1] && previousDataEx2[ccy2] ) {
    //     console.log(previousDataEx1[ccy1]['best_bid'])
    //     console.log(previousDataEx2[ccy2]['best_ask'])
    // }
    // console.log(ccy2)
    // console.log(previousDataEx2[ccy2])
    // console.log(previousDataEx1)
    // console.log(ccy1,ccy2)
    // console.log(lastData[exchange1][ccy1]['best_bid'][0])

    // console.log(previousDataEx1)
    // If both previous data exist, compare them
    let bestBidEx1, bestBidSzEx1, bestAskEx1, bestAskSzEx1;
    let bestBidEx2, bestBidSzEx2, bestAskEx2, bestAskSzEx2;

    if (previousDataEx1[ccy1] && previousDataEx2[ccy2]) {
        bestBidEx1 = previousDataEx1[ccy1]['best_bid'][0];
        bestBidSzEx1 = previousDataEx1[ccy1]['best_bid'][1];
        bestAskEx1 = previousDataEx1[ccy1]['best_ask'][0];
        bestAskSzEx1 = previousDataEx1[ccy1]['best_ask'][1];

        bestBidEx2 = previousDataEx2[ccy2]['best_bid'][0];
        bestBidSzEx2 = previousDataEx2[ccy2]['best_bid'][1];
        bestAskEx2 = previousDataEx2[ccy2]['best_ask'][0];
        bestAskSzEx2 = previousDataEx2[ccy2]['best_ask'][1];
    }
    // console.log(bestBidEx1)
    // You can now use them outside the if block

  
        
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
  
  
// Function to process data when received (this can be customized)
function onWsDataReceived(exchange, data) {
// Custom logic to process the received data
console.log(`Data received from ${exchange}:`, data);
}

// const wsServers = {
//     // 'okxperp':{'perp':`ws://localhost:5090/ws`},
//     'htxperp':{'perp':`ws://localhost:5091/ws`},
// };

// market_type_orderbook1 = document.getElementById('market-type-orderbook1').value
// currency_orderbook1 = document.getElementById('currency-input-orderbook1').value
// exchange_orderbook1 = document.getElementById('exchange1-input').value

// market_type_orderbook2 = document.getElementById('market-type-orderbook2').value
// currency_orderbook2 = document.getElementById('currency-input-orderbook2').value
// exchange_orderbook2 = document.getElementById('exchange2-input').value

// socketUrl1 =  wsServers[exchange_orderbook1+market_type_orderbook1]
// socketUrl2 =  wsServers[exchange_orderbook2][market_type_orderbook2]
const wsServers = {
    'htxperp': { 'perp': `ws://localhost:5091/ws` },
    // 'okxperp': { 'perp': `ws://localhost:5090/ws` },

    // Add others here...
};

let lastData = {};
let wsConnections = {};
let tableAssignment = {
    1: null,
    2: null
};

// === Helpers === //
function appendLastData(exchange, symbol, data) {
    if (!lastData[exchange]) lastData[exchange] = {};
    lastData[exchange][symbol] = data;
}

function getSelectedValues(tableId) {
    const market = document.getElementById(`market-type-orderbook${tableId}`).value;
    const currency = document.getElementById(`currency-input-orderbook${tableId}`).value;
    const exchange = document.getElementById(`exchange${tableId}-input`).value;
    return { market, currency, exchange };
}

function isAssigned(exchange, symbol, tableId) {
    const { market, currency, exchange: selectedExchange } = getSelectedValues(tableId);
    return exchange === `${selectedExchange}${market}` && symbol === currency;
}

function handleData(exchange, symbol, data) {
    appendLastData(exchange, symbol, data);
    if (isAssigned(exchange, symbol, 1)) {
        populateOrderBook(1, exchange, data);
    } else if (isAssigned(exchange, symbol, 2)) {
        populateOrderBook(2, exchange, data);
    }
}

const market_type_orderbook1 = document.getElementById('market-type-orderbook1').value;
const currency_orderbook1 = document.getElementById('currency-input-orderbook1').value;
const exchange_orderbook1 = document.getElementById('exchange1-input').value;
const json_dict = {
    symbol: "BTC-USD",
    market_type: "PERP",
    exchange_type: 'okxperp'
};


// === WebSocket Connection === //
function connectToSocketIO() {
    Object.entries(wsServers).forEach(([exchangeKey, marketTypes]) => {
        Object.entries(marketTypes).forEach(([marketType, wsUrl]) => {
            if (!wsUrl) return;

            const socket = new WebSocket(wsUrl);
            socket.onopen = () => {
                console.log(`[${exchangeKey}] Connected: ${wsUrl}`);
                socket.send("Client connected and ready");
                socket.send("start")
            };



            socket.onmessage = (event) => {
                console.debug(event)
                try {
                    // console.log(json_dict)
                     
                    socket.send(JSON.stringify(json_dict))
                    // socket.send('hello')
                    // socket.send(json_dict)
                   
                } catch (err) {
                    console.warn(`[${exchangeKey}] Parse error`, err);
                }
            };

            socket.onclose = () => {
                console.log(`[${exchangeKey}] Disconnected`);
            };

            socket.onerror = (error) => {
                console.warn(`[${exchangeKey}] WebSocket Error:`, error);
            };

            wsConnections[exchangeKey] = socket;
        });
    });
}

// === UI Bindings === //
['1', '2'].forEach(tableId => {
    document.getElementById(`market-type-orderbook${tableId}`).addEventListener('change', () => {
        const { market, exchange } = getSelectedValues(tableId);
        tableAssignment[tableId] = `${exchange}${market}`;
        console.log(tableAssignment)

    });
    document.getElementById(`currency-input-orderbook${tableId}`).addEventListener('change', () => {
        const { market, exchange } = getSelectedValues(tableId);
        tableAssignment[tableId] = `${exchange}${market}`;
        console.log(tableAssignment)
    });
    document.getElementById(`exchange${tableId}-input`).addEventListener('change', () => {
        const { market, exchange } = getSelectedValues(tableId);
        tableAssignment[tableId] = `${exchange}${market}`;
        console.log(tableAssignment)

    });
    
});

// === Init === //
connectToSocketIO();


//     Object.keys(wsServers).forEach(exchange => {
//         const socketUrl = wsServers[exchange];
        
//         // console.log(socketUrl)
//         // Create a Socket.IO connection for the exchange
//         const socket = io(socketUrl, {
//             transports: ['websocket'],
//             reconnection: true,               // Enable reconnection (default: true)
//             reconnectionAttempts: 10,         // Number of attempts before giving up (default: Infinity)
//             reconnectionDelay: 1000,          // Initial delay between attempts (default: 1000 ms)
//             reconnectionDelayMax: 5000,       // Maximum delay between attempts (default: 5000 ms)
//             timeout: 20000   
//             // debug: false // Disable debug logging
//         });  // Connect to the server
        
//         // Listen for reconnection
//         socket.on("reconnect", (attemptNumber) => {
//             console.log(`Reconnected after ${attemptNumber} attempts`);
//         });

//         // Listen for reconnection attempts
//         socket.on("reconnect_attempt", (attemptNumber) => {
//             console.log(`Reconnection attempt ${attemptNumber}`);
//         });

//         // Listen for reconnection errors
//         socket.on("reconnect_error", (error) => {
//             console.error("Reconnection error:", error);
//         });

//         // Listen for reconnection failure
//         socket.on("reconnect_failed", () => {
//             console.error("Reconnection failed after all attempts");
//         });

//         // Handle Socket.IO connect event
//         socket.on('connect', () => {
//             console.log(`Connected to ${exchange} Socket.IO server at ${socketUrl}`);
//             updateStatus(exchange, true);
//         });

//         // Handle Socket.IO connection error event
//         socket.on('connect_error', (error) => {
//             console.error(`Error occurred with ${exchange} Socket.IO connection:`, error);
//         });

//         // Handle Socket.IO disconnect event
//         socket.on('disconnect', () => {
//             console.log(`Disconnected from ${exchange} Socket.IO server.`);
//             updateStatus(exchange, false);
//         });

//         // Handle incoming messages (use your custom event names for messages)
//         // find out which currency first then we connect to that ws key
//         // console.log(document.getElementById('currency-input').value )
        
//         socket.on(document.getElementById('currency-input').value, (data) => {
//             try {
//                 // console.log('data')
//                 // console.log(`Received data from ${exchange}:`, data);
//                 lastData[exchange] = data; // Store data for this exchange
//                 if (data.currency == document.getElementById('currency-input').value){
//                     // console.log(data)
//                     // console.log(data.currency)
//                     compareData(data);
//                     onWsDataReceived(exchange, data); // Handle the received data
//                 }
                
//             } catch (error) {
//                 console.error(`Error processing data from ${exchange}:`, error);
//             }
//         });

//         // Store the Socket.IO connection
//         wsConnections[exchange] = socket;
//     });
// }



// function compareDataQueue(data){
//     json_data = JSON.parse(data)
//     // console.log(json_data)
//     symbol = json_data['symbol']
//     exchange = json_data['exchange']
//     if (!lastData[exchange][symbol]) {
//         lastTrades[exchange][symbol] = []
//     }
//     lastData[exchange][symbol] =  json_data
//     // console.log(lastData)
//     compareData(lastData)

// }


// function connectToSocketIO1(socketUrl1) {
//     if (socket1) {
//         console.log("Closing old socket1 before creating a new one");
//         disconnectSocket1();
//     }

//     socket1 = new WebSocket(socketUrl1);


//     socket1.onopen = () => {
//         console.log("Connected to server:", socketUrl1);
//         socket1.send("Client connected and ready");

//     };

//     socket1.onmessage = (event) => {
//         compareDataQueue(event.data)
//         clearOrderbookTable(1);

//         populateOrderBook(1, exchange_orderbook1, event.data);
//         socket1.send("message Received");
//     };

//     socket1.onclose = () => {
//         console.log("Disconnected from server");
//     };

//     socket1.onerror = (error) => {
//         console.log("WebSocket Error: ", error);
//     };

//     // Only attach listeners once
//     if (!listenersAttached) {
//         attachListeners();
//         listenersAttached = true;
//     }

//     // Clean up on unload
//     window.addEventListener("beforeunload", () => {
//         if (socket1) socket1.close(1000, "Client left");
//     });
// }

// function attachListeners() {
//     document.getElementById('market-type-orderbook1').addEventListener('change', () => {
//         sendMarketData();
//     });

//     document.getElementById('currency-input-orderbook1').addEventListener('change', () => {
//         sendMarketData();
//     });

//     document.getElementById('exchange1-input').addEventListener('change', () => {
//         sendMarketData(true);  // force reconnect
//     });
// }

// function sendMarketData(forceReconnect = false) {
//     const market_type_orderbook1 = document.getElementById('market-type-orderbook1').value;
//     const currency_orderbook1 = document.getElementById('currency-input-orderbook1').value;
//     const exchange_orderbook1 = document.getElementById('exchange1-input').value;
//     const json_dict = {
//         symbol: currency_orderbook1,
//         market_type: market_type_orderbook1,
//         exchange_type: exchange_orderbook1
//     };

//     console.log(json_dict);

//     const socketUrl1 = wsServers[exchange_orderbook1][market_type_orderbook1];

//     if (forceReconnect) {
//         console.log("Socket readyState before reconnect:", socket1.readyState);

//         disconnectSocket1();
//         listenersAttached = false; // allow reattaching on next connect
//         connectToSocketIO1(socketUrl1);
//     } else if (socket1 && socket1.readyState === WebSocket.OPEN) {
//         clearOrderbookTable(1);
//         socket1.send(JSON.stringify(json_dict));

//     }
// }

// function disconnectSocket1() {
//     if (socket1) {
//         if (socket1.readyState === WebSocket.OPEN || socket1.readyState === WebSocket.CONNECTING) {
//             socket1.close(1000, "Manual disconnect");
//         }
//         socket1 = null;
//         console.log("Socket manually disconnected");
//     }
// }





// // Function to connect to Socket.IO servers for all exchanges
// function connectToSocketIO2(socketUrl2) {

//     socket2 = new WebSocket(socketUrl2);
//     socket2.onopen = () => {
//         console.log("Connected to server:ws://localhost:5090/ws");
        
//         socket2.send("Client connected and ready");

//     };
    
//     socket2.onmessage = (event) => {
//         compareDataQueue(event.data)
        
//         clearOrderbookTable(2)
        
//         populateOrderBook(2,exchange_orderbook2,event.data)
//         socket2.send("message Receieved")
        
//     };


//     socket2.onclose = () => {
//         console.log("Disconnected from server");
//     };

//     socket2.onerror = (error) => {
//         console.log("WebSocket Error: ", error);
//     };

//     // Send any message you like
//     function sendMessage(message) {
//         socket2.send(message);
//     }

    

 
// // Only attach listeners once
//     if (!listenersAttached2) {
//         attachListeners2();
//         listenersAttached2 = true;
//         }

//     // Clean up on unload
//     window.addEventListener("beforeunload", () => {
//         if (socket2) socket2.close(1000, "Client left");
//     });
//     }

//     function attachListeners2() {
//     document.getElementById('market-type-orderbook2').addEventListener('change', () => {
//         sendMarketData2();
//     });

//     document.getElementById('currency-input-orderbook2').addEventListener('change', () => {
//         sendMarketData2();
//     });

//     document.getElementById('exchange2-input').addEventListener('change', () => {
//         sendMarketData2(true);  // force reconnect
//     });
//     }

//     function sendMarketData2(forceReconnect = false) {
//     const market_type_orderbook2 = document.getElementById('market-type-orderbook2').value;
//     const currency_orderbook2 = document.getElementById('currency-input-orderbook2').value;
//     const exchange_orderbook2 = document.getElementById('exchange2-input').value;
//     const json_dict = {
//         symbol: currency_orderbook2,
//         market_type: market_type_orderbook2,
//         exchange_type: exchange_orderbook2
//     };

//     console.log(json_dict);

//     const socketUrl2 = wsServers[exchange_orderbook2][market_type_orderbook2];
    
//     if (forceReconnect ) {
//         disconnectSocket2(socket2);
//         // clearOrderbookTable(2);

//         connectToSocketIO2(socketUrl2);

//     } else if (socket2 && socket2.readyState === WebSocket.OPEN) {
//         clearOrderbookTable(2);
//         socket2.send(JSON.stringify(json_dict));

//     }
//     }

//     function disconnectSocket2(socket2) {
//     if (socket2 && socket2.readyState === WebSocket.OPEN) {
//         socket2.close(1000, "Manual disconnect");
//         console.log("Socket manually disconnected");
//     }
//     }






// // Function to clear old data from lastData (for memory management)
// function clearOldData() {
//     Object.keys(lastData).forEach(exchange => {
//         if (lastData[exchange] && Date.now() - lastData[exchange].timestamp > 60000) { // 1 minute timeout for data
//             lastData[exchange] = null; // Clear data if it's older than 1 minute
//             console.log(`Cleared old data for ${exchange}`);
//         }
//     });
// }
// // Periodically clear old data to manage memory
// setInterval(clearOldData, 60000); // Clear old data every 60 seconds

// connectToSocketIO1(socketUrl1)
// connectToSocketIO2(socketUrl2)
