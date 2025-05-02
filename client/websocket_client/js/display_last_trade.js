// Connect to the Flask-SocketIO server
// const htxsocketLastTrades = io(`http://${hostname}:6101`);
// const okxsocketLastTrades = io('http://localhost:5098');

let lastTrades = {
    "htxperp": {}, // 
    "htxspot": {}, // 
    "okxperp": {},  // Another exchange
    "okxspot": {},  // Another exchange
    "deribitperp":{}

};

// Function to initialize the structure for a new currency pair
function initializeCurrencyPair(exchange, instrument,currencyPair) {
    // Ensure the exchange exists
    if (!lastTrades[exchange]) {
        lastTrades[exchange] = {};
    }

    // Ensure the instrument exists
    if (!lastTrades[exchange][instrument]) {
        lastTrades[exchange][instrument] = {}
    }
     // Ensure the currency pair exists
     if (!lastTrades[exchange][instrument][currencyPair]) {
        lastTrades[exchange][instrument][currencyPair] = []
    }
}

const tradeSources = [
    { id: 1, exchange: "okx", port: 6100, suffix: "1", type: "perp" },
    { id: 2, exchange: "htx", port: 6101, suffix: "2", type: "perp" },
    { id: 3, exchange: "deribit", port: 6102, suffix: "3", type: "perp" } // Add more as needed
];



async function fetchTradeHistory({ exchange, port, suffix, id, type }) {
    const token = getAuthToken();
    const username = localStorage.getItem("username");
    const redis_key = localStorage.getItem("key");

    if (!token || !username || !redis_key) return;

    const ccyInput = document.getElementById(`currency-input-orderbook1`);
    if (!ccyInput) return;

    const ccy = ccyInput.value;
    const request_data = { username, redis_key, ccy };
    try {
        const response = await fetch(`http://${hostname}:${port}/${exchange}${type}/get_last_trades`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request_data)
        });

        if (response.ok) {
            const response_data = await response.json();
            if (response_data.error) {
                // populateLastTrades(id, true, response_data.error);
                // console.error('ERROR updating last trades',)
            } else {
                updateLastTrades(response_data.exchange, response_data.ccy, response_data.trades);
                // populateLastTrades(id);
                // console.log(lastTrades)
            }
        } else {
            console.error(`Error fetching trades for ${exchange}:`, response.statusText);
        }
    } catch (err) {
        console.error(`Fetch failed for ${exchange}:`, err);
    }
}



async function fetchTradeHistory2({ exchange, port, suffix, id, type }) {
    const token = getAuthToken();
    const username = localStorage.getItem("username");
    const redis_key = localStorage.getItem("key");

    if (!token || !username || !redis_key) return;

    const ccyInput = document.getElementById(`currency-input-orderbook2`);
    if (!ccyInput) return;

    const ccy = ccyInput.value;
    const request_data = { username, redis_key, ccy };
    try {
        const response = await fetch(`http://${hostname}:${port}/${exchange}${type}/get_last_trades`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request_data)
        });

        if (response.ok) {
            const response_data = await response.json();
            // console.log(response_data)
            if (response_data.error) {
                // console.error('ERROR updating last trades')
            } else {
                updateLastTrades(response_data.exchange, response_data.ccy, response_data.trades);
                // console.log(lastTrades)
            }
        } else {
            console.error(`Error fetching trades for ${exchange}:`, response.statusText);
        }
    } catch (err) {
        console.error(`Fetch failed for ${exchange}:`, err);
    }
}



function startLastTradeScheduler(interval =5000) {
    tradeSources.forEach(source => {
        console.log(source)
        async function schedule() {
            // console.log(source)
            await fetchTradeHistory(source);
            populateLastTrades(1)
            await fetchTradeHistory2(source);
            populateLastTrades(2)
            setTimeout(schedule, interval);

        }
        schedule(); // Start each scheduler

    });

}


document.addEventListener("DOMContentLoaded", () => {
    startLastTradeScheduler();
});






// // Function to update the last trades
function updateLastTrades(exchange, currency ,trades) {
    
    if (!lastTrades[exchange][currency]) {
        lastTrades[exchange][currency] = []
    }
    if (trades){
        trades.forEach(row=>{
            // console.log(row)
            newTrade = { "px": row['price'], "ts": row['timestamp'], "side": row['side'], "sz":row['amount'] }
            lastTrades[exchange][currency].unshift(newTrade)
            // console.log(lastTrades)
         
            if (lastTrades[exchange][currency].length > 10) {
                lastTrades[exchange][currency].pop(); // Remove oldest trade if more than 10 trades
            }
        })
        // populateLastTrades(1)
        // console.log(lastTrades)
    }
   
}


// async function getTradeHistory(){
//     const token = getAuthToken();
//     const username = localStorage.getItem('username');
//     const redis_key = localStorage.getItem('key');


//     if (!token || !username || !redis_key) {
//         // alert("You must be logged in to access this.");
//         return;
//     }
//     ccy = document.getElementById('currency-input-orderbook1').value

//     const request_data = { "username": username, "redis_key": redis_key,'ccy':ccy };

//     const firstLastTradePromise = fetch(`http://${hostname}:6100/okxperp/get_last_trades`, {
//         method: 'POST',
//         headers: {
//             'Authorization': `Bearer ${token}`,
//             'Content-Type': 'application/json',
//         },
//         body: JSON.stringify(request_data)
//     });


//     const results = await Promise.allSettled([firstLastTradePromise]);

//     // Handle OKX Response
//     if (results[0].status === 'fulfilled') {
//         const response = results[0].value;
//         if (response.ok) {
//             const response_data = await response.json();
//             if (response_data['error']){
//                 // alert('ERROR')
//                 populateLastTrades(1,error=true,errorMsg = response_data['error']) 
//             }
//             else{
//                 updateLastTrades(response_data['exchange'], response_data['ccy'] ,response_data['trades'])
//                 populateLastTrades(1) 
//             }
        
            
//         } else {
//             console.error('Error fetching OKX orders:', response.statusText);
//         }
//     } else {
//         console.error('OKX Request failed:', results[0].reason);
//     }

// }



// async function getTradeHistory2(){
//     const token = getAuthToken();
//     const username = localStorage.getItem('username');
//     const redis_key = localStorage.getItem('key');


//     if (!token || !username || !redis_key) {
//         // alert("You must be logged in to access this.");
//         return;
//     }
//     ccy = document.getElementById('currency-input-orderbook2').value

//     const request_data = { "username": username, "redis_key": redis_key,'ccy':ccy };

//     const firstLastTradePromise2 = fetch(`http://${hostname}:6101/htxperp/get_last_trades`, {
//         method: 'POST',
//         headers: {
//             'Authorization': `Bearer ${token}`,
//             'Content-Type': 'application/json',
//         },
//         body: JSON.stringify(request_data)
//     });


//     const results2 = await Promise.allSettled([firstLastTradePromise2]);

//     // Handle SECOND TABLE Response
//     if (results2[0].status === 'fulfilled') {
//         const response = results2[0].value;
//         if (response.ok) {
            
//             const response_data = await response.json();
//             if (response_data['error']){
//                 // alert('ERROR')
//                 // populateLastTrades(2,error=true,errorMsg = response_data['error']) 
//             }
//             else{
//                 updateLastTrades(response_data['exchange'], response_data['ccy'] ,response_data['trades'])
//                 // populateLastTrades(2) 
//             }
        
        
            
//         } else {
//             console.error('Error fetching SECOND TABLE trades:', response.statusText);
//         }
//     } else {
//         console.error('SECOND TABLE Request failed:', results2[0].reason);
//     }

// }

function unixTsConversionHoursMinutes(timestampString) {
    const timestamp = Number(timestampString);
    if (!timestamp || isNaN(timestamp)) {
        return "Invalid timestamp";
    }

    // Convert the timestamp to a Date object
    const date = new Date(timestamp);

    // Extract the components of the time
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    const seconds = String(date.getSeconds()).padStart(2, "0");
    const milliseconds = String(date.getMilliseconds()).padStart(3, "0");

    // Format as hh:mm:ss:ms
    return `${hours}:${minutes}:${seconds}:${milliseconds}`;
}



function populateLastTrades(tableNo,error=false,errorMsg = '') {

    let selectedExchange = document.getElementById(`exchange${tableNo}-input`).value
    const selectedCcy= document.getElementById(`currency-input-orderbook${tableNo}`).value;
    const lastTradeHeader = document.getElementById(`lastTrade-header-${tableNo}`)
    const market_type = document.getElementById(`market-type-orderbook${tableNo}`).value

    if (market_type == 'perp'){
        selectedExchange += 'perp'
    }
    else{
        selectedExchange += 'spot'
    }
    
    // console.log(selectedExchange,selectedCcy)

    data = lastTrades[selectedExchange][selectedCcy]
    lastTradeHeader.innerHTML = `Last Trades: ${selectedExchange}`
        
    const tableBody = document.getElementById(`lastprice-data-table-body-${tableNo}`);
    tableBody.innerHTML = ''
    if (error){
        tableBody.innerHTML = ''

        const row = document.createElement('tr');

        row.innerHTML = `<td colspan="3">${errorMsg}</td>`;
        tableBody.appendChild(row);
        return
    }
    // Populate table with new data
    if (data){
        data.forEach(trade => {
            const row = document.createElement('tr'); // Create a new table row
            
            // Create and append cells for price, time, direction, and amount
            row.innerHTML = `
                <td>${unixTsConversionHoursMinutes(trade.ts)}</td>

                <td class ='${trade.side}'>${Number(trade.px).toLocaleString(undefined, {minimumFractionDigits: 1,maximumFractionDigits: 1 })}</td>
                <td class='${trade.side}'>${trade.sz}</td>
            `;

            // Append the row to the table body
            tableBody.appendChild(row);
        });
    }
    }




// // // // Set up the scheduler
// // function startLastTradeScheduler(interval = 5000) {
// //     // Call getTradeHistory immediately
// //     getTradeHistory();
// //     getTradeHistory2();

// //     // Schedule getTradeHistory to run every few seconds
// //     setInterval(getTradeHistory, interval);
// //     setInterval(getTradeHistory2, interval);
// //     console.log(lastTrades)

// // }

// async function scheduleGetTradeHistory2(interval) {
//     await getTradeHistory2();
//     setTimeout(() => scheduleGetTradeHistory2(interval), interval);
// }

// async function scheduleGetTradeHistory(interval) {
//     await getTradeHistory();
//     setTimeout(() => scheduleGetTradeHistory(interval), interval);
// }

// function startLastTradeScheduler(interval = 5000) {
//     scheduleGetTradeHistory(interval);
//     scheduleGetTradeHistory2(interval);
// }


// // Start the scheduler when the page loads
// document.addEventListener('DOMContentLoaded', () => {
//     startLastTradeScheduler();
// });

// getTradeHistory();
// getTradeHistory2();

