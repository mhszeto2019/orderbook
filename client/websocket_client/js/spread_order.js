// document.addEventListener("DOMContentLoaded", function() {
//     // Selecting buttons and adding event listeners
//     document.getElementById("buy-button").addEventListener("click", buyOrder);
//     document.getElementById("sell-button").addEventListener("click", sellOrder);

//     function getOrderParams() {
//         const orderType = document.getElementById("order-type-input").value;  // Limit or Market
//         const currencyPair = document.getElementById("currency-input").value;  // BTCUSD, BTCUSDT, etc.
//         const price = parseFloat(document.getElementById("price-input").value); // Order price
//         const spread = parseFloat(document.getElementById("spread-input").value); // Spread
//         const quantity = parseFloat(document.getElementById("qty-input").value);  // Quantity to buy or sell

//         return { orderType, currencyPair, price, spread, quantity };
//     }

//     function buyOrder() {
//         const { orderType, currencyPair, price, spread, quantity } = getOrderParams();

//         // Basic validation (e.g., ensuring all fields are filled)
//         if (!orderType || !currencyPair || isNaN(price) || isNaN(spread) || isNaN(quantity)) {
//             alert("Please fill out all fields correctly before placing a buy order.");
//             return;
//         }
        
//         // API SEND Backend
//         // BUY LEG
//         // SELL LEG
//         // Logic for placing a buy order
//         console.log("Placing Buy Order with the following details:");
//         console.log(`Order Type: ${orderType}`);
//         console.log(`Currency Pair: ${currencyPair}`);
//         console.log(`Price: ${price}`);
//         console.log(`Spread: ${spread}`);
//         console.log(`Quantity: ${quantity}`);

//         // Execute buy order logic, e.g., call to backend API
//         // Example: axios.post('/api/buy', { orderType, currencyPair, price, spread, quantity });
//     }

//     function sellOrder() {
//         const { orderType, currencyPair, price, spread, quantity } = getOrderParams();

//         // Basic validation (e.g., ensuring all fields are filled)
//         if (!orderType || !currencyPair || isNaN(price) || isNaN(spread) || isNaN(quantity)) {
//             alert("Please fill out all fields correctly before placing a sell order.");
//             return;
//         }

//         // Logic for placing a sell order
//         console.log("Placing Sell Order with the following details:");
//         console.log(`Order Type: ${orderType}`);
//         console.log(`Currency Pair: ${currencyPair}`);
//         console.log(`Price: ${price}`);
//         console.log(`Spread: ${spread}`);
//         console.log(`Quantity: ${quantity}`);

//         // Execute sell order logic, e.g., call to backend API
//         // Example: axios.post('/api/sell', { orderType, currencyPair, price, spread, quantity });
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

    // Handle order form submission
    document.getElementById('order-form').onsubmit = async (event) => {
        event.preventDefault();

        const orderType = document.getElementById('order-type-input').value;
        const currency = document.getElementById('currency-input').value;
        const price = document.getElementById('price-input').value;
        const spread = document.getElementById('spread-input').value;
        const qty = document.getElementById('qty-input').value;
        const direction = event.submitter.value;
        
        // Create order object
        const orderData = {
            orderType,
            currency,
            price,
            spread,
            qty,
            direction
        };

        // Send order data to Redis
        try {
            const response = await fetch('http://localhost:5000/place_order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(orderData)
            });
            

            if (response.ok) {
                const result = await response.json();
                console.log('Order data sent to Redis successfully:', result);
            } else {
                console.error('Error sending order data to Redis:', response.statusText);
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
