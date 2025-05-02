let debounceTimeout = null;

// function populateOrderBook(i,exchange, data) {
//     const timestamp = document.getElementById(`orderbook-timestamp-${i}`);
//     // Get the selected exchange for the current table
//     const selectedExchange = document.getElementById(`exchange${i}-input`).value;
//     const orderbookHeader = document.getElementById(`orderbook-header-${i}`)
//     const scrollableOrderbook =  document.getElementById(`orderBookTable${i}`)
//     // If the selected exchange matches the current exchange from WebSocket
   
//     const tableBody = document.getElementById(`order-data-table-body-${i}`);
//     // Clear the previous data in the table
//     tableBody.innerHTML = '';
//     data = JSON.parse(data)

//     const bid_list = data.bids;
//     const ask_list = data.asks.reverse();
//     const readableTime = new Date(data.timestamp).toLocaleString();
//     timestamp.innerHTML = readableTime;
//     // timestamp.innerHTML = `${data.timestamp}`;
    
//     orderbookHeader.innerHTML = `Orderbook: ${selectedExchange.toUpperCase()}` 
//     // // Populate asks
//     ask_list.forEach(item => {
//         const row = document.createElement('tr');  // Create a new row
//         row.classList.add('asks');  // Add class 'ask' for styling purposes
//         row.innerHTML = `<td>${item[0]}</td>
//         <td>${item[1]}</td>`;
//         tableBody.appendChild(row);
//     });

//     // Add a separator row between asks and bids
//     const separatorRow = document.createElement('tr');
//     separatorRow.innerHTML = `<td colspan="2" style="border-top: 2px solid #000; text-align: center;"></td>`;

//     tableBody.appendChild(separatorRow);
//     // Populate bids
//     bid_list.forEach(item => {
//         const row = document.createElement('tr');  // Create a new row
//         row.classList.add('bids');  // Add class 'bid' for styling purposes
//         row.innerHTML = `<td>${item[0]}</td>
//                         <td>${item[1]}</td>`;
//         tableBody.appendChild(row);
//     });
// }


function populateOrderBook(i, exchange, data) {
    const timestamp = document.getElementById(`orderbook-timestamp-${i}`);
    const container = document.getElementById(`scrollable-orderbook-${i}`);
    const tableBody = document.getElementById(`order-data-table-body-${i}`);
    // let shouldScroll = !container.dataset.hasScrolled;
    shouldScrollState[i] = !container.dataset.hasScrolled;
    // console.log(shouldScrollState[i])
    // Store previous scroll state
    // Clear existing content
    tableBody.innerHTML = '';
    data = JSON.parse(data);
    const readableTime = new Date(data.timestamp).toLocaleString();
    timestamp.innerHTML = readableTime;
    // timestamp.innerHTML = `${data.timestamp}`;
    // Process asks (reverse order)
    data.asks.reverse().forEach(item => {
        tableBody.innerHTML += `<tr class="asks"><td>${item[0]}</td><td>${item[1]}</td></tr>`;
    });
    // Add separator
    tableBody.innerHTML += `<tr id="separator-row-${i}"><td colspan="2" style="border-top:2px solid #000;"></td></tr>`;
    // Process bids
    data.bids.forEach(item => {
        tableBody.innerHTML += `<tr class="bids"><td>${item[0]}</td><td>${item[1]}</td></tr>`;
    });
    // console.log(tableBody.getBoundingClientRect())
    
    // Only scroll on first load
    if (shouldScrollState[i]) {
        setTimeout(() => {
            const separator = document.getElementById(`separator-row-${i}`);
            if (separator) {
                // Calculate scroll position accounting for sticky header
                const headerHeight = container.querySelector('thead').offsetHeight;
                const separatorPos = separator.offsetTop;
                const scrollPos = separatorPos - (container.clientHeight / 2) -headerHeight/2 ;
                container.scrollTo({
                    top: scrollPos,
                    behavior: 'smooth'
                });
                
                // Mark as scrolled
                container.dataset.hasScrolled = 'true';
            }
        }, 50);
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


function clearOrderbookTable(tableNumber) {
    const orderbookTs1DOM = document.getElementById(`orderbook-timestamp-${tableNumber}`);
    const orderbookDisplay1DOM = document.getElementById(`order-data-table-body-${tableNumber}`);

    // Safely clear tables and timestamps
    if (orderbookDisplay1DOM) {
        while (orderbookDisplay1DOM.firstChild) {
            orderbookDisplay1DOM.firstChild.remove();
        }
    }
    if (orderbookTs1DOM) orderbookTs1DOM.innerHTML = '';
}



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

