// document.addEventListener("DOMContentLoaded", function() {
//     // Selecting buttons and adding event listeners
//     document.getElementById("buy-button").addEventListener("click", buyOrder);
//     document.getElementById("sell-button").addEventListener("click", sellOrder);

//     function getOrderParams() {
//         const ordType = document.getElementById("order-type-input").value;  // Limit or Market
//         const currencyPair = document.getElementById("currency-input").value;  // BTCUSD, BTCUSDT, etc.
//         const price = parseFloat(document.getElementById("price-input").value); // Order price
//         const spread = parseFloat(document.getElementById("spread-input").value); // Spread
//         const quantity = parseFloat(document.getElementById("qty-input").value);  // Quantity to buy or sell

//         return { ordType, currencyPair, price, spread, quantity };
//     }

//     function buyOrder() {
//         const { ordType, currencyPair, price, spread, quantity } = getOrderParams();

//         // Basic validation (e.g., ensuring all fields are filled)
//         if (!ordType || !currencyPair || isNaN(price) || isNaN(spread) || isNaN(quantity)) {
//             alert("Please fill out all fields correctly before placing a buy order.");
//             return;
//         }
        
//         // API SEND Backend
//         // BUY LEG
//         // SELL LEG
//         // Logic for placing a buy order
//         console.log("Placing Buy Order with the following details:");
//         console.log(`Order Type: ${ordType}`);
//         console.log(`Currency Pair: ${currencyPair}`);
//         console.log(`Price: ${price}`);
//         console.log(`Spread: ${spread}`);
//         console.log(`Quantity: ${quantity}`);

//         // Execute buy order logic, e.g., call to backend API
//         // Example: axios.post('/api/buy', { ordType, currencyPair, price, spread, quantity });
//     }

//     function sellOrder() {
//         const { ordType, currencyPair, price, spread, quantity } = getOrderParams();

//         // Basic validation (e.g., ensuring all fields are filled)
//         if (!ordType || !currencyPair || isNaN(price) || isNaN(spread) || isNaN(quantity)) {
//             alert("Please fill out all fields correctly before placing a sell order.");
//             return;
//         }

//         // Logic for placing a sell order
//         console.log("Placing Sell Order with the following details:");
//         console.log(`Order Type: ${ordType}`);
//         console.log(`Currency Pair: ${currencyPair}`);
//         console.log(`Price: ${price}`);
//         console.log(`Spread: ${spread}`);
//         console.log(`Quantity: ${quantity}`);

//         // Execute sell order logic, e.g., call to backend API
//         // Example: axios.post('/api/sell', { ordType, currencyPair, price, spread, quantity });
//     }
// });



// spread_order.js
// spread_order.js
document.addEventListener('DOMContentLoaded', () => {


    // Function to update price data on the UI
    function updatePriceData(data) {
        console.log("Received Price Update:", data);

        // Update UI with the latest prices
        const btcusdtPriceElement = document.getElementById('btcusdt-price');
        const btcusdPriceElement = document.getElementById('btcusd-price');

        if (data.BTCUSDT) {
            btcusdtPriceElement.innerText = `BTC/USDT: ${data.BTCUSDT.price}`;
        }
        
        if (data.BTCUSD) {
            btcusdPriceElement.innerText = `BTC/USD: ${data.BTCUSD.price}`;
        }
    }
    
    document.addEventListener('DOMContentLoaded', function () {
        const marketTab = document.getElementById('market-tab');
        const limitTab = document.getElementById('limit-tab');
        const ordTypeInput = document.getElementById('order-type-input');
        
        // Set the default order type to "market" when the page first loads
        ordTypeInput.value = 'market';
    
        // Set the order type to "market" when the Market tab is selected
        marketTab.addEventListener('click', function () {
            ordTypeInput.value = 'market';
        });
    
        // Set the order type to "limit" when the Limit tab is selected
        limitTab.addEventListener('click', function () {
            ordTypeInput.value = 'limit';
        });
    });
    
    

    // Handle order form submission
    document.getElementById('order-form').onsubmit = async (event) => {
        event.preventDefault();
        const leadingExchange = document.getElementById('leading-exchange-input').value;
        const laggingExchange = document.getElementById('lagging-exchange-input').value;

        const ordType = document.getElementById('order-type-input').value;
        const instId = document.getElementById('currency-input').value;
        const px = document.getElementById('price-input').value;
        const spread = document.getElementById('spread-input').value;
        const sz = document.getElementById('qty-input').value;
        const side = event.submitter.value;
        console.log(
            leadingExchange,
            laggingExchange,
            ordType,
            instId,
            px,
            spread,
            sz,
            side
        )
        // Create order object
        const orderData = {
            leadingExchange,
            laggingExchange,
            ordType,
            instId,
            px,
            spread,
            sz,
            side
        };

        // Send order data to Redis

        try {
            // console.log(ordType)
            console.log(orderData)
            if (ordType == 'market'){
                const response = await fetch('http://localhost:5024/place_market_order', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(orderData)
                });
                if (response.ok) {
                    const result = await response.json();
                    console.log(result)
                    console.log('Response from server:',result.data[0].sMsg);
                } else {
                    console.error('Error sending order data to Redis:', response.statusText);
                }

               
            }
            else {
                // if ordType == limit
                const response = await fetch('http://localhost:5024/place_limit_order', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(orderData)
                });
                if (response.ok) {
                    const result = await response.json();
               

                    console.log('Response from server:',result.data[0].sMsg);
                } else {
                    console.error('Error sending order data to Redis:', response.statusText);
                }

              
            }
            
        } catch (error) {
            console.error('Error while sending order data to Redis:', error);
        }
    };

    // Add a refresh button functionality for transaction history or open orders
    document.getElementById('txn-history-refresh-btn').onclick = async () => {
        try {
            const response = await fetch('/get_transaction_history');
            const historyData = await response.json();
            // Update the transaction history table here
            updateTransactionHistoryTable(historyData);
        } catch (error) {
            console.error('Error fetching transaction history:', error);
        }
    };

    // Function to update transaction history table
    function updateTransactionHistoryTable(data) {
        const txnHistoryBody = document.getElementById('oms-open-txn-history-body');
        txnHistoryBody.innerHTML = ''; // Clear existing rows

        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.currency}</td>
                <td>${item.filledPrice}</td>
                <td>${item.filledSize}</td>
                <td>${item.filledTime}</td>
                <td>${item.tradeType}</td>
                <td>${item.fee}</td>
                <td>${item.feeCurrency}</td>
                <td>${item.timestamp}</td>
            `;
            txnHistoryBody.appendChild(row);
        });
    }
});
