

// Store the WebSocket connections
const wsConnections = {};

// Store the exchange data for each exchange
const lastData = {
    'okxperp': {},
    'okxspot':{},
    'htxperp': {},
    'binanceperp':{},
    'binancespot':{},
    'deribitperp':{}
};


function updateArbOrder(buySpreadpx,buysz,sellSpreadpx,sellsz,buysellgap){
    // console.log(buySpreadpx,buysz,sellSpreadpx,sellsz,buysellgap)
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
    // console.log('comparingdata')
    // const exchange = newData.exchange;
    // // const otherExchange = exchange === 'htx' ? 'okx' : 'htx';
    let exchange1 = document.getElementById('exchange1-input').value
    let exchange2 = document.getElementById('exchange2-input').value
    let marketType1 = document.getElementById('market-type-orderbook1').value
    let marketType2 = document.getElementById('market-type-orderbook2').value
    let ccy1 = document.getElementById('currency-input-orderbook1').value
    let ccy2 = document.getElementById('currency-input-orderbook2').value
    
    if (!exchange1 || !exchange2 || !marketType1 || !marketType2 || !ccy1 || !ccy2) {
        console.warn("Missing input values");
        return;
    }

    // // Get the previous data for the current exchange and the other exchange
    if (marketType1 == 'futures'){
        exchange1 = exchange1 + 'futures'
    }
    else{
        exchange1 = exchange1 + 'spot'

    }

    if (marketType2 == 'futures'){
        exchange2 = exchange2 + 'futures'
    }
    else{
        exchange2 = exchange2 + 'spot'

    }

    const previousDataEx1 = lastData[exchange1];
    const previousDataEx2 = lastData[exchange2];

    
    // If both previous data exist, compare them
    let bestBidEx1, bestBidSzEx1, bestAskEx1, bestAskSzEx1;
    let bestBidEx2, bestBidSzEx2, bestAskEx2, bestAskSzEx2;
    // console.log(bestBidEx2, bestBidSzEx2, bestAskEx2, bestAskSzEx2)

    if (ccy1 == '--Not Selected--' | ccy2 == '--Not Selected--'){
        return
    }

    if (previousDataEx1?.[ccy1]) {
        if (marketType1 == 'futures'){
            bestBidEx1 = previousDataEx1[ccy1]['best_bid'][0][0];
            bestBidSzEx1 = previousDataEx1[ccy1]['best_bid'][0][1];
            bestAskEx1 = previousDataEx1[ccy1]['best_ask'][0][0];
            bestAskSzEx1 = previousDataEx1[ccy1]['best_ask'][0][1];
    
        }
        else if(marketType1 =='spot'){
            bestBidEx1 = previousDataEx1[ccy1]['best_bid'][0][0];
            bestBidSzEx1 = previousDataEx1[ccy1]['best_bid'][0][1]*bestBidEx1/100;
            bestBidSzEx1 = Number((previousDataEx1[ccy1]['best_bid'][0][1] * bestBidEx1 / 100).toFixed(2));
            bestAskEx1 = previousDataEx1[ccy1]['best_ask'][0][0];
            // bestAskSzEx1 = previousDataEx1[ccy1]['best_ask'][0][1]*bestAskEx1/100;
            bestAskSzEx1 = Number((previousDataEx1[ccy1]['best_ask'][0][1] * bestAskEx1 / 100).toFixed(2));
            // console.log(bestBidSzEx1,bestAskSzEx1)
        }
     
    }
    // if (ccy2 != '--Not Selected--' && previousDataEx2[ccy2]){
    if (previousDataEx2?.[ccy2]){
    
        if (marketType2 == 'futures'){
            bestBidEx2 = previousDataEx2[ccy2]['best_bid'][0][0];
            bestBidSzEx2 = previousDataEx2[ccy2]['best_bid'][0][1];
            bestAskEx2 = previousDataEx2[ccy2]['best_ask'][0][0];
            bestAskSzEx2 = previousDataEx2[ccy2]['best_ask'][0][1];
        }
        else if (marketType2 =='spot'){
            bestBidEx2 = previousDataEx2[ccy2]['best_bid'][0][0];
            // bestBidSzEx2 = previousDataEx2[ccy2]['best_bid'][0][1]*bestBidEx2/100;
            bestBidSzEx2 = Number((previousDataEx2[ccy2]['best_bid'][0][1]*bestBidEx2/100).toFixed(2));

            bestAskEx2 = previousDataEx2[ccy2]['best_ask'][0][0];
            // bestAskSzEx2 = previousDataEx2[ccy2]['best_ask'][0][1]*bestAskEx2/100;
            bestAskSzEx2 = Number((previousDataEx2[ccy2]['best_ask'][0][1]*bestAskEx2/100).toFixed(2));

        }

      
    }


        // console.log(bestBidEx2, bestBidSzEx2, bestAskEx2, bestAskSzEx2)
        
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

const wsServers = {
    'okx':{'futures':`ws://${hostname}:5091/ws`,'spot':''},
    'htx':{'futures':`ws://${hostname}:5091/ws2`,'spot':''},
    'deribit':{'futures':`ws://${hostname}:5091/ws3`,'spot':''},
    'binance':{'futures':`ws://${hostname}:5091/ws4`,'spot':`ws://${hostname}:5091/ws5`},

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
let listenersAttached1= false;
let listenersAttached2 = false;

function compareDataQueue(data){
    // console.log(data)
    json_data = JSON.parse(data)
    // console.log(json_data)
    symbol = json_data['symbol']
    exchange = json_data['exchange']

    if (!exchange){
        // console.log("NO DATA FOUND")
    }

    if (!lastData[exchange]) {
        lastData[exchange] = {symbol:[]}
        // console.log(lastData)
    }
    if (!lastData[exchange][symbol]) {
        lastData[exchange][symbol] = []
    }
    lastData[exchange][symbol] =  json_data
    compareData(lastData)

}
// {"symbol": "BTC-USD-SWAP", "bids": [[96352.7, 6230.0], [96352.3, 3.0], [96352.1, 1.0], [96352.0, 73.0], [96351.6, 1.0], [96351.4, 123.0], [96351.2, 2.0], [96351.0, 1.0], [96350.7, 1.0], [96350.0, 74.0]], "asks": [[96352.8, 16242.0], [96352.9, 50.0], [96353.0, 1.0], [96353.1, 1.0], [96353.7, 843.0], [96354.0, 1.0], [96354.6, 300.0], [96354.8, 920.0], [96354.9, 1.0], [96355.1, 2.0]], "timestamp": 1746172780226, "best_bid": [[96352.7, 6230.0]], "best_ask": [[96352.8, 16242.0]], "exchange": "binanceperp"}

// {"symbol": "BTC-USD-SWAP", "bids": [[96358.0, 1757.0, 0], [96357.6, 4.0, 0], [96357.4, 200.0, 0], [96356.0, 72.0, 0], [96353.2, 71.0, 0]], "asks": [[96358.1, 4584.0, 0], [96359.8, 349.0, 0], [96359.9, 662.0, 0], [96360.0, 72.0, 0], [96360.1, 1092.0, 0]], "timestamp": 1746172767605, "best_bid": [[96358.0, 1757.0, 0]], "best_ask": [[96358.1, 4584.0, 0]], "exchange": "okxperp"}



// Function to connect to Socket.IO servers for all exchanges
function connectToSocketIO1(socketUrl1) {

    socket1 = new WebSocket(socketUrl1);
    socket1.onopen = () => {
        console.log("Connected to server:ws://localhost:5090");
        // socket2.send(JSON.parse({"action":"start"}));
        input_data = {"action":"start",
                    "ccy":document.getElementById('currency-input-orderbook1').value,
                    "exchange":document.getElementById('exchange1-input').value,
                    "market_type":document.getElementById('market-type-orderbook1').value
                     }

        socket1.send(JSON.stringify(input_data));
        // socket2.send("Client connected and ready");
    };
    
    socket1.onmessage = (event) => {
        // console.log(event.data)
        
        compareDataQueue(event.data)
        populateOrderBook(1,exchange_orderbook1,event.data)
        // socket2.send(JSON.stringify({"action":"ping","ccy":document.getElementById('currency-input-orderbook2').value}))
        
    };

    socket1.onclose = () => {
        input_data = {"action":"stop",
            "ccy":document.getElementById('currency-input-orderbook1').value,
            "exchange":document.getElementById('exchange1-input').value,
            "market_type":document.getElementById('market-type-orderbook1').value
             }

        socket1.send(JSON.stringify(input_data));

        console.log("Disconnected from server");
    };

    socket1.onerror = (error) => {
        console.log("WebSocket Error: ", error);
    };

// Only attach listeners once
    if (!listenersAttached1) {
        attachListeners1();
        listenersAttached1 = true;
        }

    // Clean up on unload
    window.addEventListener("beforeunload", () => {
        if (socket1) socket1.close(1000, "Client left");
    });
    }

    function attachListeners1() {
    document.getElementById('market-type-orderbook1').addEventListener('change', () => {
        sendMarketData1();
    });

    document.getElementById('currency-input-orderbook1').addEventListener('change', () => {
        sendMarketData1();
    });

    document.getElementById('exchange1-input').addEventListener('change', () => {
        sendMarketData1();  // force reconnect
    });
    }

    function sendMarketData1(forceReconnect = false) {
    const market_type_orderbook1 = document.getElementById('market-type-orderbook1').value;
    const currency_orderbook1 = document.getElementById('currency-input-orderbook1').value;
    const exchange_orderbook1 = document.getElementById('exchange1-input').value;
    let json_dict = {
        action: "change",
        ccy: currency_orderbook1,
        market_type: market_type_orderbook1,
        exchange: exchange_orderbook1
    };

    repopulateArbBtnData()
    const socketUrl1 = wsServers[exchange_orderbook1][market_type_orderbook1];
    
    if (forceReconnect ) {
        disconnectSocket1(socket1);
        // clearOrderbookTable(2);

        connectToSocketIO1(socketUrl1);

    } else if (socket1 && socket1.readyState === WebSocket.OPEN) {
        clearOrderbookTable(1);
        socket1.send(JSON.stringify(json_dict));

    }
    }

    function disconnectSocket1(socket1) {
    if (socket1 && socket1.readyState === WebSocket.OPEN) {
        socket1.close(1000, "Manual disconnect");
        console.log("Socket manually disconnected");
    }
    }



// Function to connect to Socket.IO servers for all exchanges
function connectToSocketIO2(socketUrl2) {

    socket2 = new WebSocket(socketUrl2);
    socket2.onopen = () => {
        console.log("Connected to server:ws://localhost:5091/ws");
        // socket2.send(JSON.parse({"action":"start"}));
        input_data = {"action":"start",
                    "ccy":document.getElementById('currency-input-orderbook2').value,
                    "exchange":document.getElementById('exchange2-input').value,
                    "market_type":document.getElementById('market-type-orderbook2').value
                     }

        socket2.send(JSON.stringify(input_data));
        // socket2.send("Client connected and ready");
    };
    
    socket2.onmessage = (event) => {
        compareDataQueue(event.data)
        // clearOrderbookTable(2)
        populateOrderBook(2,exchange_orderbook2,event.data)
        // socket2.send(JSON.stringify({"action":"ping","ccy":document.getElementById('currency-input-orderbook2').value}))
        
    };

    socket2.onclose = () => {
        input_data = {"action":"stop",
            "ccy":document.getElementById('currency-input-orderbook2').value,
            "exchange":document.getElementById('exchange2-input').value,
            "market_type":document.getElementById('market-type-orderbook2').value
             }

        socket2.send(JSON.stringify(input_data));

        console.log("Disconnected from server");
    };

    socket2.onerror = (error) => {
        console.error("WebSocket Error: ", error);
    };

// Only attach listeners once
    if (!listenersAttached2) {
        attachListeners2();
        listenersAttached2 = true;
        }

    // Clean up on unload
    window.addEventListener("beforeunload", () => {
        if (socket2) socket2.close(1000, "Client left");
    });
    }

    function attachListeners2() {
    document.getElementById('market-type-orderbook2').addEventListener('change', () => {
        sendMarketData2();

    });

    document.getElementById('currency-input-orderbook2').addEventListener('change', () => {
        sendMarketData2();

    });

    document.getElementById('exchange2-input').addEventListener('change', () => {
        sendMarketData2();  // force reconnect

    });
    }

    function sendMarketData2(forceReconnect = false) {
    const market_type_orderbook2 = document.getElementById('market-type-orderbook2').value;
    const currency_orderbook2 = document.getElementById('currency-input-orderbook2').value;
    const exchange_orderbook2 = document.getElementById('exchange2-input').value;
    const json_dict = {
        action: "change",
        ccy: currency_orderbook2,
        market_type: market_type_orderbook2,
        exchange: exchange_orderbook2
    };
    repopulateArbBtnData()


    // console.log(json_dict);

    const socketUrl2 = wsServers[exchange_orderbook2][market_type_orderbook2];
    
    if (forceReconnect ) {
        disconnectSocket2(socket2);
        // clearOrderbookTable(2);

        connectToSocketIO2(socketUrl2);

    } else if (socket2 && socket2.readyState === WebSocket.OPEN) {
        clearOrderbookTable(2);
        socket2.send(JSON.stringify(json_dict));

    }
    }

    function disconnectSocket2(socket2) {
    if (socket2 && socket2.readyState === WebSocket.OPEN) {
        socket2.close(1000, "Manual disconnect");
        console.log("Socket manually disconnected");
    }
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

connectToSocketIO1(socketUrl1)
connectToSocketIO2(socketUrl2)
