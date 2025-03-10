let debounceTimeout = null;

function populateOrderBook(exchange, data) {
    // Loop through each table (orderbook 1 and orderbook 2)
    for (let i = 1; i <= 2; i++) {
        const timestamp = document.getElementById(`orderbook-timestamp-${i}`);
        // Get the selected exchange for the current table
        const selectedExchange = document.getElementById(`selected-exchange-orderbook-${i}`).innerText;
        // If the selected exchange matches the current exchange from WebSocket
        if (selectedExchange === exchange) {
            const tableBody = document.getElementById(`order-data-table-body-${i}`);
            // Clear the previous data in the table
            tableBody.innerHTML = '';

            const bid_list = JSON.parse(data.bid_list);
            const ask_list = JSON.parse(data.ask_list);
            timestamp.innerHTML = `<b>Ts(${exchange})</b>:\n ${data.timestamp}`;
            // Populate asks
            ask_list.forEach(item => {
                const row = document.createElement('tr');  // Create a new row
                row.classList.add('asks');  // Add class 'ask' for styling purposes
                row.innerHTML = `<td>${Number(item.price).toLocaleString()}</td><td>${item.size}</td>`;
                tableBody.appendChild(row);
            });
            // Add a separator row between asks and bids
            const separatorRow = document.createElement('tr');
            separatorRow.innerHTML = `<td colspan="2" style="border-top: 2px solid #000; text-align: center;"></td>`;
            tableBody.appendChild(separatorRow);
            // Populate bids
            bid_list.forEach(item => {
                const row = document.createElement('tr');  // Create a new row
                row.classList.add('bids');  // Add class 'bid' for styling purposes
                row.innerHTML = `<td>${Number(item.price).toLocaleString()}</td><td>${item.size}</td>`;
                tableBody.appendChild(row);
            });
        }
    }
}

// Debounce function that delays execution of populateOrderBook
function debounce(func, delay) {
    return function (...args) {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => func(...args), delay);
    };
}

// Create a debounced version of populateOrderBook with a delay of 10 ms
const debouncedPopulateOrderBook = debounce(populateOrderBook, 10);


function clearOrderbookTable() {

    const orderbookTs1DOM = document.getElementById('orderbook-timestamp-1');
    const orderbookTs2DOM = document.getElementById('orderbook-timestamp-2');

    const orderbookDisplay1DOM = document.getElementById('order-data-table-body-1');
    const orderbookDisplay2DOM = document.getElementById('order-data-table-body-2');

    // Safely clear tables and timestamps
    if (orderbookDisplay1DOM) {
        while (orderbookDisplay1DOM.firstChild) {
            orderbookDisplay1DOM.firstChild.remove();
        }
    }
    if (orderbookDisplay2DOM) {
        while (orderbookDisplay2DOM.firstChild) {
            orderbookDisplay2DOM.firstChild.remove();
        }
    }

    if (orderbookTs1DOM) orderbookTs1DOM.innerHTML = '';
    if (orderbookTs2DOM) orderbookTs2DOM.innerHTML = '';
}

function clearlastPriceTable() {

    const lastpriceTs1DOM = document.getElementById('lastprice-timestamp-1');
    const lastpriceTs2DOM = document.getElementById('lastprice-timestamp-2');

    const lastpriceDisplay1DOM = document.getElementById('lastprice-data-table-body-1');
    const lastpriceDisplay2DOM = document.getElementById('lastprice-data-table-body-2');

    // Safely clear tables and timestamps
    if (lastpriceDisplay1DOM) {
        while (lastpriceDisplay1DOM.firstChild) {
            lastpriceDisplay1DOM.firstChild.remove();
        }
    }
    if (lastpriceDisplay2DOM) {
        while (lastpriceDisplay2DOM.firstChild) {
            lastpriceDisplay2DOM.firstChild.remove();
        }
    }

    if (lastpriceTs1DOM) lastpriceTs1DOM.innerHTML = '';
    if (lastpriceTs2DOM) lastpriceTs2DOM.innerHTML = '';

    
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
    clearlastPriceTable()

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
    clearlastPriceTable()

    const exchange1 = document.getElementById('exchange1-input').value
    const exchange2 = document.getElementById('exchange2-input').value
    const ccy = document.getElementById('currency-input').value

    const lastpriceexch1 = document.getElementById('selected-exchange-lastprice-1')
    const ordertableexch1 = document.getElementById('selected-exchange-orderbook-1')
    const lastpriceexch2 = document.getElementById('selected-exchange-lastprice-2')
    const ordertableexch2 = document.getElementById('selected-exchange-orderbook-2')
    // Get the selected value from the select input

    // Update the display with the selected currency
    if (lastpriceexch1) lastpriceexch1.innerHTML = exchange1;
    if (ordertableexch1) ordertableexch1.innerHTML = exchange1;
    if (lastpriceexch2) lastpriceexch2.innerHTML = exchange2;
    if (ordertableexch2) ordertableexch2.innerHTML = exchange2;

}

window.onload = function() {
    updateCurrency()
    updateExchange()
    console.log("The document has finished loading!");
};