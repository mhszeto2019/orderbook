let debounceTimeout = null;


function populateOrderBook(i,exchange, data) {
    // console.log(exchange)

    const timestamp = document.getElementById(`orderbook-timestamp-${i}`);
    // Get the selected exchange for the current table
    const selectedExchange = document.getElementById(`exchange${i}-input`).value;
    const orderbookHeader = document.getElementById(`orderbook-header-${i}`)
    const scrollableOrderbook =  document.getElementById(`orderBookTable${i}`)
    // If the selected exchange matches the current exchange from WebSocket
   
    const tableBody = document.getElementById(`order-data-table-body-${i}`);
    // Clear the previous data in the table
    tableBody.innerHTML = '';
    data = JSON.parse(data)

    const bid_list = data.bids;
    const ask_list = data.asks.sort();
    timestamp.innerHTML = `${data.timestamp}`;
    
    orderbookHeader.innerHTML = `Orderbook: ${selectedExchange.toUpperCase()}` 
    // // Populate asks
    ask_list.forEach(item => {
        const row = document.createElement('tr');  // Create a new row
        row.classList.add('asks');  // Add class 'ask' for styling purposes
        row.innerHTML = `<td>${item[0]}</td>
        <td>${item[1]}</td>`;
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
        row.innerHTML = `<td>${item[0]}</td>
                        <td>${item[1]}</td>`;
        tableBody.appendChild(row);
    });

      
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

// Function to scroll the orderbook to the middle

// Call the scrollToMiddle function when the page loads (or after content is updated)



function clearlastPriceTable() {

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

}

function updateExchange(){
    clearOrderbookTable()
    clearlastPriceTable()
  
}

window.onload = function() {
    updateCurrency()
    updateExchange()
    console.log("The document has finished loading!");
};