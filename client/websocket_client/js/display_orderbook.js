let debounceTimeout = null;


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
    if (!data || !data.asks || !data.bids){
        return 
    }

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

