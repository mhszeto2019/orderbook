// oms-open-orders-body


async function populateOpenOrders() {
    const openOpenOrderDOM = document.getElementById('oms-open-orders-body');
    openOpenOrderDOM.innerHTML = '';  // Clear the table before populating
    const openOpenOrderTS = document.getElementById('last-updated-orders');
    updateTime(openOpenOrderTS);  // Update the timestamp of when the data was last fetched

    const token = getAuthToken();
    const username = localStorage.getItem('username');
    const redis_key = localStorage.getItem('key');

    if (!token || !username || !redis_key) {
        alert("You must be logged in to access this.");
        return;
    }

    const request_data = { "username": username, "redis_key": redis_key };

    // Set up both the OKX and HTX requests
    const firstOrderPromise = fetch(`http://${hostname}:5080/okx/get_all_open_orders`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request_data)
    });

    const secondOrderPromise = fetch(`http://${hostname}:5081/htx/get_all_open_orders`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request_data)
    });

    try {
        const results = await Promise.allSettled([firstOrderPromise, secondOrderPromise]);

        // Array to hold combined orders
        let allOpenOrders = [];

        // Handle OKX Response
        if (results[0].status === 'fulfilled') {
            const response = results[0].value;
            if (response.ok) {
                const response_data = await response.json();
                if (response_data.data){
                    console.log('OKX data:', response_data.data);
                    // Append OKX data to allOpenOrders
                    allOpenOrders = allOpenOrders.concat(response_data.data.map(position => ({
                        ...position,
                        exchange: 'OKX'  // Add exchange name to each position
                    })));
                    console.log('OKX populated');
                }
                else{
                    console.error(response_data['msg'],response_data['code'])
                }
                
            } else {
                console.error('Error fetching OKX orders:', response.statusText);
            }
        } else {
            console.error('OKX Request failed:', results[0].reason);
        }

        // Handle HTX Response
        if (results[1].status === 'fulfilled') {
            const response = results[1].value;
            if (response.ok) {
                const response_data = await response.json();
                console.log('HTX data:', response_data);
                const formattedData = Htx2OkxFormat(response_data);  // Format HTX data as needed
                // Append HTX data to allOpenOrders
                allOpenOrders = allOpenOrders.concat(formattedData.map(position => ({
                    ...position,
                    exchange: 'HTX'  // Add exchange name to each position
                })));
                console.log('HTX populated');
            } else {
                console.error('Error fetching HTX orders:', response.statusText);
            }
        } else {
            console.error('HTX Request failed:', results[1].reason);
        }

        // After both responses are handled, populate the table with all orders
        populateOpenOpenOrdersTable(allOpenOrders);

    } catch (error) {
        console.error('Error in fetching and populating data:', error);
    }
}

const ordersHist = {}

function populateOpenOpenOrdersTable(orders) {
    // Get reference to the DataTable instance (or initialize if not already)
    const openordersTable = $('.OpenOrdersTable').DataTable();

    // Clear existing rows from DataTable
    openordersTable.clear();

    if (orders.length === 0) {
        console.log(orders.length);

        // Manually add a row with `colspan`
        const emptyMessage = `
            <tr>
                <td colspan="11" class="text-center text-muted">No open orders available</td>
            </tr>`;
        $('#oms-open-orders-body').html(emptyMessage);
    } else {
        // Add rows dynamically
        orders.forEach(position => {
            // Check attachAlgoOrds
            console.log(position)
            ordersHist[position.ordId]={};
            ordersHist[position.ordId]['orderPx']= position.px;
            ordersHist[position.ordId]['orderSz']= position.sz;
            
            const algoData = Array.isArray(position.attachAlgoOrds) && position.attachAlgoOrds.length > 0
                ? position.attachAlgoOrds.map(algo => {
                    // Update the ordersHist object
                    if (!ordersHist[position.ordId]) {
                        ordersHist[position.ordId] = {};
                    }
                    ordersHist[position.ordId]['stop_limit'] = algo.slTriggerPx || 'N/A';
                    ordersHist[position.ordId]['take_profit'] = algo.tpTriggerPx || 'N/A';
                    ordersHist[position.ordId]['algo_id'] = algo.attachAlgoId || 'N/A';
                    
                    // Return the HTML representation for this algo data
                    return `
                        ${algo.attachAlgoId}
                        <div style="width: 150px;">
                            <span>SL Trigger Px: ${algo.slTriggerPx || 'N/A'}</span><br>
                            <span>TP Trigger Px: ${algo.tpTriggerPx || 'N/A'}</span>
                        </div>
                    `;
                }).join('') // Combine multiple algo data into one cell
                : "No data";
            openordersTable.row.add([
                position.exchange || 'N/A',  // New exchange column
                position.instId || 'N/A',
                position.lever || 'N/A',
                position.side || 'N/A',
                position.px || 'N/A',
                position.sz ? Number.parseFloat(position.sz).toFixed(1) : 'N/A',
                algoData,  // Display attachAlgoOrds content
                position.ordId || 'N/A',
                position.cTime ? new Date(parseInt(position.cTime)).toLocaleString() : 'N/A',
                // Buttons for last two columns
                `<button class="btn btn-primary btn-sm" data-order-id="${position.ordId}" data-algo-id="${ordersHist[position.ordId]['algo_id']}" onclick="handleModify('${position.instId}', '${position.ordId}','${ordersHist[position.ordId]['algo_id']}')">Modify</button>`,
                `<button class="btn btn-danger btn-sm" data-order-id="${position.ordId}" data-algo-id="${ordersHist[position.ordId]['algo_id']}" onclick="handleDelete('${position.instId}', '${position.ordId}','${ordersHist[position.ordId]['algo_id']}')">Delete</button>`
            ]);
        });
        console.log(ordersHist)
    }

    // Redraw the table to reflect changes
    openordersTable.draw();
}

function handleModify(instId, ordId,algoId) {
    // Get the modal element
    const modal = document.getElementById('modifyPositionModal');

    // Reference the form inside the modal
    const form = document.getElementById('modifyPositionForm');

    // Clear any existing content in the form
    form.innerHTML = '';

    // Dynamically add form fields for modification
    form.innerHTML = `
       <div class="container">
    <!-- Row 1: IDs with Copy Buttons -->
    <div class="row mb-3">
        <div class="col-md-4">
            <label for="instId" class="form-label">Instrument ID</label>
            <div class="input-group">
                <input type="text" class="form-control form-control-sm" id="instId" name="instId" value="${instId}" readonly>
                <button type="button" class="btn btn-outline-secondary btn-sm" onclick="copyToClipboard('instId')">
                    <i class="bi bi-clipboard"></i>
                </button>
            </div>
        </div>
        <div class="col-md-4">
            <label for="ordId" class="form-label">Order ID</label>
            <div class="input-group">
                <input type="text" class="form-control form-control-sm" id="ordId" name="ordId" value="${ordId}" readonly>
                <button type="button" class="btn btn-outline-secondary btn-sm" onclick="copyToClipboard('ordId')">
                    <i class="bi bi-clipboard"></i>
                </button>
            </div>
        </div>
        <div class="col-md-4">
            <label for="algoId" class="form-label">Algo ID</label>
            <div class="input-group">
                <input type="text" class="form-control form-control-sm" id="algoId" name="algoId" value="${algoId}" readonly>
                <button type="button" class="btn btn-outline-secondary btn-sm" onclick="copyToClipboard('algoId')">
                    <i class="bi bi-clipboard"></i>
                </button>
            </div>
        </div>
    </div>

    <!-- Row 2: Order Size and Price -->
    <div class="row mb-3">
        <div class="col-md-6">
            <label for="orderSize" class="form-label">Order Size</label>
            <input type="number" step="0.01" class="form-control" id="orderSize" value="${ordersHist[ordId]['orderSz']}" name="orderSize" placeholder="Enter new order size">
        </div>
        <div class="col-md-6">
            <label for="orderPrice" class="form-label">Order Price</label>
            <input type="number" step="0.01" class="form-control" id="orderPrice" value="${ordersHist[ordId]['orderPx']}" name="orderPrice" placeholder="Enter new order price">
        </div>
    </div>

    <!-- Row 3: Stop Loss and Take Profit -->
    <div class="row mb-3">
        <div class="col-md-6">
            <label for="stopLoss" class="form-label">Stop Loss (SL)</label>
            <input type="number" step="0.01" class="form-control" id="stopLoss" value="${ordersHist[ordId]?.['stop_limit'] || 'None'}" name="stopLoss" placeholder="Enter new SL price">
        </div>
        <div class="col-md-6">
            <label for="takeProfit" class="form-label">Take Profit (TP)</label>
            <input type="number" step="0.01" class="form-control" id="takeProfit" value="${ordersHist[ordId]?.['take_profit'] || 'None'}" name="takeProfit" placeholder="Enter new TP price">
        </div>
    </div>
</div>



    `;
    // Display the modal
    modal.style.display = 'block';
    populateOpenOrders();

}

// Function to close the modal
function closeModifyOrderModal() {
    const modal = document.getElementById('modifyPositionModal');
    modal.style.display = 'none';
}

document.getElementById('modifyPositionForm').addEventListener('submit', async function (event) {
    // Prevent the default form submission (which causes a page refresh)
    event.preventDefault();

    // Close the modal
    closeModifyOrderModal();

    // Optional: Add your logic for handling the form submission here
    const formData = new FormData(this); // Collect form data 

    const token = getAuthToken();
    const username = localStorage.getItem('username');
    const redis_key = localStorage.getItem('key');

    if (!token || !username || !redis_key) {
        alert("You must be logged in to access this.");
        return;
    }
    console.log(formData)

    const request_data = { "username": username, "redis_key": redis_key, 'ordId':formData.get('ordId'),'algoId':formData.get('algoId'),'px':formData.get('orderPrice'),'sz':formData.get('orderSize'),'ccy':formData.get('instId'),'exchange':'okx','stopLoss':formData.get('stopLoss'),'takeProfit':formData.get('takeProfit'),'orderPrice':formData.get('orderPrice')};
    // console.log('Form submitted with data:', Object.fromEntries(request_data));

    const firstAmmendPromise = fetch(`http://${hostname}:5080/okx/ammend_order`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request_data)
    });
    try {
        const results = await Promise.allSettled([firstAmmendPromise]);

        // Array to hold combined orders
        let allOpenOrders = [];

        // Handle OKX Response
        if (results[0].status === 'fulfilled') {
            const response = results[0].value;
            if (response.ok) {
                const response_data = await response.json();
                if (response_data.data){
                    console.log('OKX data:', response_data.data);
                    // Append OKX data to allOpenOrders
                    allOpenOrders = allOpenOrders.concat(response_data.data.map(position => ({
                        ...position,
                        exchange: 'OKX'  // Add exchange name to each position
                    })));
                    console.log('OKX populated');
                }
                else{
                    console.error(response_data['msg'],response_data['code'])
                }
                
            } else {
                console.error('Error fetching OKX orders:', response.statusText);
            }
        } else {
            console.error('OKX Request failed:', results[0].reason);
        }

        // Handle HTX Response
        // if (results[1].status === 'fulfilled') {
        //     const response = results[1].value;
        //     if (response.ok) {
        //         const response_data = await response.json();
        //         console.log('HTX data:', response_data);
        //         const formattedData = Htx2OkxFormat(response_data);  // Format HTX data as needed
        //         // Append HTX data to allOpenOrders
        //         allOpenOrders = allOpenOrders.concat(formattedData.map(position => ({
        //             ...position,
        //             exchange: 'HTX'  // Add exchange name to each position
        //         })));
        //         console.log('HTX populated');
        //     } else {
        //         console.error('Error fetching HTX orders:', response.statusText);
        //     }
        // } else {
        //     console.error('HTX Request failed:', results[1].reason);
        // }

        // // After both responses are handled, populate the table with all orders
        // // populateOpenOpenOrdersTable(allOpenOrders);

    } catch (error) {
        console.error('Error in fetching and populating data:', error);
    }



});



function handleDelete(instId, ordId) {
    console.log(`Delete clicked for InstID: ${instId}, OrderID: ${ordId}`);
    // Add your delete logic here
}


// Lock state variable
let isLocked = true;

function toggleLockClear() {
    const lockButton = document.getElementById('lock-clear-btn');
    const actionButtons = document.querySelectorAll('button[id^="positions-clear-"]');

    if (isLocked) {
        // Unlock: Enable the buttons and update the lock button appearance
        lockButton.textContent = '🔓 Unlock';
        lockButton.classList.remove('btn-secondary');
        lockButton.classList.add('btn-success');
        actionButtons.forEach(button => button.disabled = false);
        isLocked = false;
    } else {
        // Lock: Disable the buttons and update the lock button appearance
        lockButton.textContent = '🔒 Lock';
        lockButton.classList.remove('btn-success');
        lockButton.classList.add('btn-secondary');
        actionButtons.forEach(button => button.disabled = true);
        isLocked = true;
    }
}

function clearPositions(exchange) {
    console.log(exchange)
    const selectedCurrency = document.getElementById('clearCurrencyDropdown').value;
    const action = `Clear positions for ${exchange} ${
        selectedCurrency === 'all' ? 'across all currencies' : `in currency: ${selectedCurrency}`
    }`;
    console.log(confirm)
    if (confirm(`Are you sure you want to ${action}? This action cannot be undone.`)) {
        console.log(action);
        // Add clearing logic here
    } else {
        console.log('Action canceled.');
    }
}
function copyToClipboard(inputId) {
    const input = document.getElementById(inputId);
    if (input) {
        input.select();
        input.setSelectionRange(0, 99999); // For mobile devices
        navigator.clipboard.writeText(input.value)
            .then(() => {
                alert(`Copied: ${input.value}`);
            })
            .catch(err => {
                console.error('Failed to copy:', err);
            });
    }
}


// async function closeOpenOrder(posId,ccy,exchange) {
//     // Data for the API (example, modify as needed)
//     const token = getAuthToken();
//     const username = localStorage.getItem('username')
//     const redis_key = localStorage.getItem('key')
//     if (!token |!username | !redis_key ) {
//         alert("You must be logged in to access this.");
//         return;
//     }
    
//     request_data = {"username":username,"redis_key":redis_key,'posId':posId,'ccy':ccy,'exchange':exchange}

  
//     // Call the API using fetch
//     const firstOrderPromise =  fetch(`http://${hostname}:5080/close_orders`, {
//         method: 'POST',
//         headers: {
//             'Authorization': `Bearer ${token}`,
//             'Content-Type': 'application/json',
//         },
//         body: JSON.stringify(request_data)
//     });

//     const results = await Promise.allSettled([firstOrderPromise]);
//     if (results[0].status === 'fulfilled') {
//         // Extract the data from the resolved promise
//         const response = results[0].value;
//         if (response.ok) {
//             // Parse the JSON data from the response
//             const response_data = await response.json();
//             console.log(response_data.data)
//             // populateOpenOpenOrdersTable(response_data.data);
//             populateOpenOrders();
//         } else {
//             console.error('Error fetching orders:', response.statusText);
//         }
//     } else {
//         console.error('Request failed:', results[0].reason);
//     }
// }

function Htx2OkxFormat(originalDataArray) {
    return originalDataArray.map(originalData => {
        console.log(originalData)
      return {
        "adl": String(originalData.open_adl || '0'),  // Convert to string, or default to 0
        "availPos": "",  // Empty as per the target format
        "avgPx": String(originalData.last_price.toFixed(1)),  // Rounded to 1 decimal place
        "baseBal": "",
        "baseBorrowed": "",
        "baseInterest": "",
        "bePx": String(originalData.liq_px.toFixed(10)),  // Displaying the value with 10 decimal points
        "bizRefId": "",
        "bizRefType": "",
        "cTime": new Date(originalData.store_time).getTime().toString(),  // Convert to timestamp
        "ccy": originalData.symbol,
        "clSpotInUseAmt": "",
        "closeOrderAlgo": [],
        "deltaBS": "",
        "deltaPA": "",
        "fee": String(originalData.profit_rate.toFixed(10)),  // Rounding for consistency
        "fundingFee": "0",
        "gammaBS": "",
        "gammaPA": "",
        "idxPx": String(originalData.cost_open.toFixed(10)),  // Using cost_open for idxPx
        "imr": "",
        "instId": originalData.contract_code + "-SWAP",  // Assuming this is a swap contract
        "instType": "SWAP",
        "interest": "",
        "last": String(originalData.last_price.toFixed(1)),
        "lever": String(originalData.lever_rate),
        "liab": "",
        "liabCcy": "",
        "liqPenalty": "0",
        "liqPx": String(originalData.liq_px.toFixed(10)),
        "margin": String(originalData.position_margin.toFixed(10)),
        "markPx": String(originalData.last_price.toFixed(1)),
        "maxSpotInUseAmt": "",
        "mgnMode": "isolated",
        "mgnRatio": "46.53351821356301",  // Assumed fixed value for this example
        "mmr": String((originalData.profit / originalData.cost_hold).toFixed(10)),  // Just an example calculation
        "notionalUsd": "100",  // Assumed fixed value
        "optVal": "",
        "pendingCloseOrdLiabVal": "",
        "pnl": String(originalData.profit.toFixed(10)),  // Placeholder, may depend on further logic
        "pos": "-1",  // Placeholder for position status
        "posCcy": "",
        "posId": "2019681002234920961",  // Placeholder position ID
        "posSide": String((originalData.direction)),  // Assumed position side
        "quoteBal": "",
        "quoteBorrowed": "",
        "quoteInterest": "",
        "realizedPnl": String(originalData.profit.toFixed(10)),
        "spotInUseAmt": "",
        "spotInUseCcy": "",
        "thetaBS": "",
        "thetaPA": "",
        "tradeId": "333006380",  // Placeholder trade ID
        "uTime": new Date(originalData.store_time).getTime().toString(),
        "upl": String(originalData.profit.toFixed(10)),
        "uplLastPx": String(originalData.profit.toFixed(10)),
        "uplRatio": String((originalData.profit_rate).toFixed(10)),
        "uplRatioLastPx": String((originalData.profit_rate).toFixed(10)),
        "usdPx": "",
        "vegaBS": "",
        "vegaPA": "",
        "exchange":'htx'
      };
    });
  }


function updateTime(selectedDOM) {
    const now = new Date();

    // Format time as HH:MM:SS AM/PM
    const hours = now.getHours();
    const minutes = now.getMinutes();
    const seconds = now.getSeconds();

    const formattedTime = `${hours % 12 || 12}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')} ${hours >= 12 ? 'PM' : 'AM'}`;

    // Display the formatted time in an element with id="time-display"
    const timeDisplay = selectedDOM
    if (timeDisplay) {
        timeDisplay.textContent = formattedTime;
    }
}


// // // // Set up the scheduler
// function startOpenOrderScheduler(interval = 5000) {
//     // Call populateOpenOrders immediately
//     populateOpenOrders();

//     // Schedule populateOpenOrders to run every few seconds
//     setInterval(populateOpenOrders, interval);
// }

// // Start the scheduler when the page loads
// document.addEventListener('DOMContentLoaded', () => {
//     startOpenOrderScheduler();
// });