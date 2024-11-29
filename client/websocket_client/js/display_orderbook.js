function populateOrderBook(exchange, data) {
    // console.log(exchange,data)
    // Loop through each table (orderbook 1 and orderbook 2)
    for (let i = 1; i <= 2; i++) {
        const timestamp = document.getElementById(`orderbook-timestamp-${i}`)
        // Get the selected exchange for the current table
        const selectedExchange = document.getElementById(`selected-exchange-orderbook-${i}`).innerText;
        // If the selected exchange matches the current exchange from WebSocket
        if (selectedExchange === exchange) {
            const tableBody = document.getElementById(`order-data-table-body-${i}`);
            // Clear the previous data in the table
            tableBody.innerHTML = '';
            
            const bid_list = JSON.parse(data.bid_list);
            const ask_list = JSON.parse(data.ask_list);
            timestamp.innerHTML = `<b>Timestamp(${exchange})</b>:\n ${data.timestamp}`;
            // Populate asks
            ask_list.forEach(item => {
                const row = document.createElement('tr');  // Create a new row
                row.classList.add('asks');  // Add class 'ask' for styling purposes
                row.innerHTML = `<td>${item.price}</td><td>(${item.size})</td>`;
                tableBody.appendChild(row);
            });
            // Populate bids
            bid_list.forEach(item => {
                const row = document.createElement('tr');  // Create a new row
                row.classList.add('bids');  // Add class 'bid' for styling purposes
                row.innerHTML = `<td>${item.price}</td><td>(${item.size})</td>`;
                tableBody.appendChild(row);
            });
        }
    }
}
function clearOrderbookTable(){
    orderbookTs1DOM = document.getElementById('orderbook-timestamp-1')
    orderbookTs2DOM = document.getElementById('orderbook-timestamp-2')

    orderbookDisplay1DOM = document.getElementById('order-data-table-body-1')
    orderbookDisplay2DOM = document.getElementById('order-data-table-body-2')
    orderbookDisplay1DOM.innerHTML=""
    orderbookDisplay2DOM.innerHTML=""

    orderbookTs1DOM.innerHTML=""
    orderbookTs2DOM.innerHTML=""
}

function onWsDataReceived(exchange,message) {
    try {
        populateOrderBook(exchange,message)
    
    } catch (error) {
        console.error("Error processing WebSocket data:", error);
    }
}


function updateCurrency() {
    clearOrderbookTable()
    // Get the currency input element
    const currencyInput = document.getElementById('currency-input');
    const lastpricepx1 = document.getElementById('selected-ccy-lastprice-1')
    const ordertablepx1 = document.getElementById('selected-ccy-orderbook-1')
    const lastpricepx2 = document.getElementById('selected-ccy-lastprice-2')
    const ordertablepx2 = document.getElementById('selected-ccy-orderbook-2')
    // Get the selected value from the select input
    const selectedCurrency = currencyInput.value;

    // Update the display with the selected currency
    lastpricepx1.innerHTML = selectedCurrency;
    ordertablepx1.innerHTML = selectedCurrency;
    lastpricepx2.innerHTML = selectedCurrency;
    ordertablepx2.innerHTML = selectedCurrency;

    // Optionally, log the selected value to the console for testing
    console.log('Selected currency:', selectedCurrency);
}

function updateExchange(){
    clearOrderbookTable()

    const exchange1 = document.getElementById('exchange1-input').value
    const exchange2 = document.getElementById('exchange2-input').value

    const lastpriceexch1 = document.getElementById('selected-exchange-lastprice-1')
    const ordertableexch1 = document.getElementById('selected-exchange-orderbook-1')
    const lastpriceexch2 = document.getElementById('selected-exchange-lastprice-2')
    const ordertableexch2 = document.getElementById('selected-exchange-orderbook-2')
    // Get the selected value from the select input

    // Update the display with the selected currency
    lastpriceexch1.innerHTML = exchange1;
    ordertableexch1.innerHTML = exchange1;
    lastpriceexch2.innerHTML = exchange2;
    ordertableexch2.innerHTML = exchange2;

}

window.onload = function() {
    updateCurrency()
    updateExchange()
    console.log("The document has finished loading!");
};