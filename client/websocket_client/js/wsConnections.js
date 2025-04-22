

// Store the WebSocket connections
const wsConnections = {};

// Store the exchange data for each exchange
const lastData = {
    'okx': null,
    'htx': null,
    'bnb': null
};


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
    'okx':{'perp':`ws://localhost:5090/ws`,'spot':''},
    'htx':{'perp':`ws://localhost:5091/ws`,'spot':''},
    

};

market_type_orderbook1 = document.getElementById('market-type-orderbook1').value
currency_orderbook1 = document.getElementById('currency-input-orderbook1').value
exchange_orderbook1 = document.getElementById('exchange1-input').value

market_type_orderbook2 = document.getElementById('market-type-orderbook2').value
currency_orderbook2 = document.getElementById('currency-input-orderbook2').value
exchange_orderbook2 = document.getElementById('exchange2-input').value

socketUrl1 =  wsServers[exchange_orderbook1][market_type_orderbook1]
socketUrl2 =  wsServers[exchange_orderbook2][market_type_orderbook2]



let socket2 = null 
let socket1 = null;

// Only attach listeners once
let listenersAttached = false;

function connectToSocketIO1(socketUrl1) {
    socket1 = new WebSocket(socketUrl1);

    socket1.onopen = () => {
        console.log("Connected to server:", socketUrl1);
    };

    socket1.onmessage = (event) => {
        clearOrderbookTable(1);
        populateOrderBook(1, exchange_orderbook1, event.data);
        socket1.send("message Received");
    };

    socket1.onclose = () => {
        console.log("Disconnected from server");
    };

    socket1.onerror = (error) => {
        console.log("WebSocket Error: ", error);
    };

    // Only attach listeners once
    if (!listenersAttached) {
        attachListeners();
        listenersAttached = true;
    }

    // Clean up on unload
    window.addEventListener("beforeunload", () => {
        if (socket1) socket1.close(1000, "Client left");
    });
}

function attachListeners() {
    document.getElementById('market-type-orderbook1').addEventListener('change', () => {
        sendMarketData();
    });

    document.getElementById('currency-input-orderbook1').addEventListener('change', () => {
        sendMarketData();
    });

    document.getElementById('exchange1-input').addEventListener('change', () => {
        sendMarketData(true);  // force reconnect
    });
}

function sendMarketData(forceReconnect = false) {
    const market_type_orderbook1 = document.getElementById('market-type-orderbook1').value;
    const currency_orderbook1 = document.getElementById('currency-input-orderbook1').value;
    const exchange_orderbook1 = document.getElementById('exchange1-input').value;
    const json_dict = {
        symbol: currency_orderbook1,
        market_type: market_type_orderbook1,
        exchange_type: exchange_orderbook1
    };

    console.log(json_dict);

    const socketUrl1 = wsServers[exchange_orderbook1][market_type_orderbook1];

    if (forceReconnect && socket1) {
        disconnectSocket1(socket1);
        connectToSocketIO1(socketUrl1);
    } else if (socket1 && socket1.readyState === WebSocket.OPEN) {
        clearOrderbookTable(1);
        socket1.send(JSON.stringify(json_dict));
    }
}

function disconnectSocket1(socket) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close(1000, "Manual disconnect");
        console.log("Socket manually disconnected");
    }
}






// Function to connect to Socket.IO servers for all exchanges
function connectToSocketIO2(socketUrl2) {
  

    socket2 = new WebSocket(socketUrl2);
    socket2.onopen = () => {
        console.log("Connected to server:ws://localhost:5090/ws");
    };
        
    socket2.onopen = () => {
        // console.log("Connected to server");
        // socket1.send("Client connected and ready");
    };

    socket2.onmessage = (event) => {
        // console.log("Received from server:", event.data);
        // acknowledge message receive from server
        // console.log(event.data)
        // console.log(typeof event.data)
        clearOrderbookTable(2)
        populateOrderBook(2,exchange_orderbook2,event.data)
        socket2.send("message Receieved")
        
    };


    socket2.onclose = () => {
        console.log("Disconnected from server");
    };

    socket2.onerror = (error) => {
        console.log("WebSocket Error: ", error);
    };

    // Send any message you like
    function sendMessage(message) {
        socket2.send(message);
    }

    

    //  // Set up button click event listener
    // Set up button 1 click event listener
    document.getElementById('market-type-orderbook2').addEventListener('change', () => {
        market_type_orderbook2 = document.getElementById('market-type-orderbook2').value
        currency_orderbook2 = document.getElementById('currency-input-orderbook2').value
        exchange_orderbook2 = document.getElementById('exchange2-input').value
        json_dict = {"symbol":currency_orderbook2,"market_type":market_type_orderbook2,"exchange_type":exchange_orderbook2}

        clearOrderbookTable(2)
        sendMessage(JSON.stringify(json_dict));

    });

    // Set up button 2 click event listener
    document.getElementById('currency-input-orderbook2').addEventListener('change', () => {
        market_type_orderbook2 = document.getElementById('market-type-orderbook2').value
        currency_orderbook2 = document.getElementById('currency-input-orderbook2').value
        exchange_orderbook2 = document.getElementById('exchange2-input').value
        json_dict = {"symbol":currency_orderbook2,"market_type":market_type_orderbook2,"exchange_type":exchange_orderbook2}
        clearOrderbookTable(2)
        sendMessage(JSON.stringify(json_dict));

    });



    // Optional cleanup on page unload
    window.addEventListener("beforeunload", () => {
        if (socket2) socket2.close(1000, "Client left");
    });

}

function disconnectSocket2(socket2) {
    if (socket2) {
        socket2.close(1000, "Manual disconnect");
        console.log("Socket manually disconnected");
    }
}


// Set up button 3 click event listener
// CHANGE EXCHANGE 
document.getElementById('exchange2-input').addEventListener('change', () => {
    market_type_orderbook2 = document.getElementById('market-type-orderbook2').value
    currency_orderbook2 = document.getElementById('currency-input-orderbook2').value
    exchange_orderbook2 = document.getElementById('exchange2-input').value
    json_dict = {"symbol":currency_orderbook2,"market_type":market_type_orderbook2,"exchange_type":exchange_orderbook2}
    socketUrl2 = wsServers[exchange_orderbook2][market_type_orderbook2]
    disconnectSocket2(socket2)
    connectToSocketIO2(socketUrl2)
});







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

connectToSocketIO1(socketUrl1)
connectToSocketIO2(socketUrl2)
