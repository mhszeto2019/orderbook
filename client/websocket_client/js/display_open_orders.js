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
    const firstOrderPromise = fetch(`http://${hostname}:5080/okx/get_all_okx_open_orders`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request_data)
    });

    const secondOrderPromise= fetch(`http://${hostname}:6061/htx/swap/get_all_htx_open_orders`, {
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
                    // Append OKX data to allOpenOrders
                    allOpenOrders = allOpenOrders.concat(response_data.data.map(position => ({
                        ...position,
                        exchange: 'OKX'  // Add exchange name to each position
                    })));
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
                const formattedData = await Htx2OkxFormatOrders(response_data);  // Format HTX data as needed
                // Append HTX data to allOpenOrders
                allOpenOrders = allOpenOrders.concat(formattedData.map(position => ({
                    ...position,
                    exchange: 'HTX'  // Add exchange name to each position
                })));
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
            ordersHist[position.ordId]={};
            ordersHist[position.ordId]['orderPx']= position.px;
            ordersHist[position.ordId]['orderSz']= position.sz;
            ordersHist[position.ordId]['side']= position.side;

            console.log(position)
            const algoData = Array.isArray(position.attachAlgoOrds) && position.attachAlgoOrds.length > 0
                ? position.attachAlgoOrds.map(algo => {
                    // Update the ordersHist object
                    if (!ordersHist[position.ordId]) {
                        ordersHist[position.ordId] = {};
                    }
                    ordersHist[position.ordId]['stop_limit'] = algo.slTriggerPx || 'N/A';
                    ordersHist[position.ordId]['take_profit'] = algo.tpOrdPx || 'N/A';
                    ordersHist[position.ordId]['algo_id'] = algo.attachAlgoId || 'N/A';
                    
                    // Return the HTML representation for this algo data
                    return `
                        <div style="width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${algo.attachAlgoId}">
                            ${algo.attachAlgoId}
                        </div>
                        <div style="width: 150px;">
                            <span>SL Trigger Px: ${algo.slTriggerPx || 'N/A'}</span><br>
                            <span>TP Order Px: ${algo.tpOrdPx || 'N/A'}</span>
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
                `<button class="btn btn-primary btn-sm" data-order-id="${position.ordId}" data-algo-id="${ordersHist[position.ordId]['algo_id']}" onclick="handleModify('${position.instId}', '${position.ordId}','${ordersHist[position.ordId]['algo_id']}','${position.exchange}')">Modify</button>`,
                `<button class="btn btn-danger btn-sm" data-order-id="${position.ordId}" data-algo-id="${ordersHist[position.ordId]['algo_id']}" onclick="handleDelete('${position.instId}', '${position.ordId}','${ordersHist[position.ordId]['algo_id']}','${position.exchange}')">Delete</button>`
            ]);
        });
    }

    // Redraw the table to reflect changes
    openordersTable.draw();
}

function handleModify(instId, ordId,algoId,exchange) {
    // Get the modal element
    const modal = document.getElementById('modifyPositionModal');

    // Reference the form inside the modal
    const form = document.getElementById('modifyPositionForm');

    // Clear any existing content in the form
    form.innerHTML = '';

    // Dynamically add form fields for modification
    form.innerHTML = `
    <div class="row mb-3">
        <!-- Exchange -->
        <div class="col-md-3">
            <label for="exchange" class="form-label">Exchange</label>
            <div class="input-group">
                <input type="text" class="form-control form-control-sm" id="exchange" name="exchange" value="${exchange}" readonly>
            </div>
        </div>
        
        <!-- CCY (Instrument ID) -->
        <div class="col-md-3">
            <label for="instId" class="form-label">CCY</label>
            <div class="input-group">
                <input type="text" class="form-control form-control-sm" id="instId" name="instId" value="${instId}" readonly>
            </div>
        </div>
        
        <!-- Order ID -->
        <div class="col-md-3">
            <label for="ordId" class="form-label">Order ID</label>
            <div class="input-group">
                <input type="text" class="form-control form-control-sm" id="ordId" name="ordId" value="${ordId}" readonly>
                <button type="button" class="btn btn-outline-secondary btn-sm" onclick="copyToClipboard('ordId')" title="Copy Order ID">
                    <i class="bi bi-clipboard"></i>
                </button>
            </div>
        </div>
        
        <!-- Algo ID -->
        <div class="col-md-3">
            <label for="algoId" class="form-label">Algo ID</label>
            <div class="input-group">
                <input type="text" class="form-control form-control-sm" id="algoId" name="algoId" value="${algoId}" readonly>
                <button type="button" class="btn btn-outline-secondary btn-sm" onclick="copyToClipboard('algoId')" title="Copy Algo ID">
                    <i class="bi bi-clipboard"></i>
                </button>
            </div>
        </div>
    </div>


    <!-- Row 2: Order Size and Price -->
    <div class="row mb-3">
        <div class="col-md-4">
            <label for="side" class="form-label">Order Side</label>
            <select class="form-control form-control-sm" id="side" name="side">
                <option value="buy" ${ordersHist[ordId]['side'] === 'buy' ? 'selected' : ''}>Buy</option>
                <option value="sell" ${ordersHist[ordId]['side'] === 'sell' ? 'selected' : ''}>Sell</option>
            </select>
        </div>

        <div class="col-md-4">
            <label for="orderSize" class="form-label">Order Size</label>
            <input type="number" step="0.01" class="form-control" id="orderSize" value="${ordersHist[ordId]['orderSz']}" name="orderSize" placeholder="Enter new order size">
        </div>
        <div class="col-md-4">
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
    const exchange = formData.get('exchange').toLowerCase()
    const request_data = { "username": username, "redis_key": redis_key, 'ordId':formData.get('ordId'),'algoId':formData.get('algoId'),'px':formData.get('orderPrice'),'sz':formData.get('orderSize'),'ccy':formData.get('instId'),'exchange':'okx','stopLoss':formData.get('stopLoss'),'takeProfit':formData.get('takeProfit'),'orderPrice':formData.get('orderPrice'),'exchange':exchange,'side':formData.get('side')};
    if (exchange == 'okx'){
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
                            // Append OKX data to allOpenOrders
                            allOpenOrders = allOpenOrders.concat(response_data.data.map(position => ({
                                ...position,
                                exchange: 'OKX'  // Add exchange name to each position
                            })));
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
            } catch (error) {
                console.error('Error in fetching and populating data:', error);
            }
    }
    else if (exchange == 'htx'){
        const firstAmmendPromise = fetch(`http://${hostname}:6061/htx/swap/ammend_order`, {
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
                            // Append OKX data to allOpenOrders
                            allOpenOrders = allOpenOrders.concat(response_data.data.map(position => ({
                                ...position,
                                exchange: 'HTX'  // Add exchange name to each position
                            })));
                        }
                        else{
                            console.error(response_data['msg'],response_data['code'])
                        }
                        
                    } else {
                        console.error('Error fetching HTX orders:', response.statusText);
                    }
                } else {
                    console.error('HTX Request failed:', results[0].reason);
                }
            } catch (error) {
                console.error('Error in fetching and populating data:', error);
            }
    }
        
    populateOpenOrders();
    



});



async function handleDelete(instId, ordId,algoId,exchange) {
    // Add your delete logic here
    exchange = exchange.toLowerCase()
    const token = getAuthToken();
    const username = localStorage.getItem('username')
    const redis_key = localStorage.getItem('key')
    if (!token |!username | !redis_key ) {
        alert("You must be logged in to access this.");
        return;
    }
    request_data = {"username":username,"redis_key":redis_key,'ordId':ordId,'ccy':instId,'exchange':exchange}
    if (exchange == 'okx')
        {
            // Call the API using fetch
            const firstOrderPromise =  fetch(`http://${hostname}:5080/okx/cancel_order_by_id`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request_data)
            });

            const results = await Promise.allSettled([firstOrderPromise]);
            if (results[0].status === 'fulfilled') {
                // Extract the data from the resolved promise
                const response = results[0].value;
                if (response.ok) {
                    // Parse the JSON data from the response
                    const response_data = await response.json();
                    // populateOpenOpenOrdersTable(response_data.data);
                    populateOpenOrders();
                } else {
                    console.error('Error fetching orders:', response.statusText);
                }
            } else {
                console.error('Request failed:', results[0].reason);
            }
        }
    else if (exchange == 'htx'){
            // Call the API using fetch
            const firstOrderPromise =  fetch(`http://${hostname}:6061/htx/swap/cancel_order_by_id`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request_data)
            });

            const results = await Promise.allSettled([firstOrderPromise]);
            if (results[0].status === 'fulfilled') {
                // Extract the data from the resolved promise
                const response = results[0].value;
                if (response.ok) {
                    // Parse the JSON data from the response
                    const response_data = await response.json();
                    // populateOpenOpenOrdersTable(response_data.data);
                    populateOpenOrders();
                } else {
                    console.error('Error fetching orders:', response.statusText);
                }
            } else {
                console.error('Request failed:', results[0].reason);
            }
        }
}

// Lock state variable
let isLocked = true;

function toggleLockClear() {
    const lockButton = document.getElementById('lock-clear-btn');
    const actionButtons = document.querySelectorAll('button[id^="positions-clear-"]');

    if (isLocked) {
        // Unlock: Enable the buttons and update the lock button appearance
        lockButton.textContent = '🔓 Lock';
        lockButton.classList.remove('btn-secondary');
        lockButton.classList.add('btn-success');
        actionButtons.forEach(button => button.disabled = false);
        isLocked = false;
    } else {
        // Lock: Disable the buttons and update the lock button appearance
        lockButton.textContent = '🔒 Unlock';
        lockButton.classList.remove('btn-success');
        lockButton.classList.add('btn-secondary');
        actionButtons.forEach(button => button.disabled = true);
        isLocked = true;
    }
}

async function clearPositions(exchange) {
    ccy = document.getElementById('clearCurrencyDropdown').value
    const selectedCurrency = document.getElementById('clearCurrencyDropdown').value;
    const action = `Clear positions for ${exchange} ${
        selectedCurrency === 'all' ? 'across all currencies' : `in currency: ${selectedCurrency}`
    }`;
    
    if (confirm(`Are you sure you want to ${action}? This action cannot be undone.`)) {
        // Add clearing logic here
        const token = getAuthToken();
        const username = localStorage.getItem('username')
        const redis_key = localStorage.getItem('key')
        if (!token |!username | !redis_key ) {
            alert("You must be logged in to access this.");
            return;
        }
        request_data = {"username":username,"redis_key":redis_key,'ccy':ccy}

        if (exchange == 'okx'){
            // Call the API using fetch
            const firstOrderPromise =  fetch(`http://${hostname}:5080/okx/cancel_all_orders_by_ccy`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request_data)
                });
    
                const results = await Promise.allSettled([firstOrderPromise]);
                if (results[0].status === 'fulfilled') {
                    // Extract the data from the resolved promise
                    const response = results[0].value;
                    if (response.ok) {
                        // Parse the JSON data from the response
                        const response_data = await response.json();
                        if (response_data['data'].length == 0){
                            alert(response_data['msg'] + "\nError code:"+ response_data['code'])
                        }
                        // populateOpenOpenOrdersTable(response_data.data);
                        populateOpenOrders();
                    } else {
                        console.error('Error fetching orders:', response.statusText);
                    }
                } else {
                    console.error('Request failed:', results[0].reason);
                }
        }
        else if (exchange == 'htx'){
            // Call the API using fetch
                const firstOrderPromise =  fetch(`http://${hostname}:6061/htx/swap/cancel_all_htx_open_order_by_ccy`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request_data)
                });
    
                const results = await Promise.allSettled([firstOrderPromise]);
                if (results[0].status === 'fulfilled') {
                    // Extract the data from the resolved promise
                    const response = results[0].value;
                    if (response.ok) {
                        // Parse the JSON data from the response
                        const response_data = await response.json();
                        if (response_data['err_msg']){
                            alert(response_data['err_msg'] + "\nError:" + response_data['err_code'])
                        }

                        // populateOpenOpenOrdersTable(response_data.data);
                        populateOpenOrders();
                    } else {
                        console.error('Error fetching orders:', response.statusText);
                    }
                } else {
                    console.error('Request failed:', results[0].reason);
                }
        }
        // ALL REMEMBER TO CHANGE WHEN ADD NEWEXCHANGE
        else{
                const firstOrderPromise =  fetch(`http://${hostname}:5080/okx/cancel_all_orders_by_ccy`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request_data)
                });

                const secondOrderPromise =  fetch(`http://${hostname}:6061/htx/swap/cancel_all_htx_open_order_by_ccy`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(request_data)
                    });
    
                const results = await Promise.allSettled([firstOrderPromise,secondOrderPromise]);
                if (results[0].status === 'fulfilled') {
                    // Extract the data from the resolved promise
                    const response = results[0].value;
                    if (response.ok) {
                        // Parse the JSON data from the response
                        const response_data = await response.json();

                        if (response_data['data'].length == 0){
                            alert(response_data['msg'] + "\nError code:"+ response_data['code'])
                        }
                        // populateOpenOpenOrdersTable(response_data.data);
                        populateOpenOrders();
                    } else {
                        console.error('Error fetching orders:', response.statusText);
                    }
                } else {
                    console.error('Request failed:', results[0].reason);
                }
                if (results[1].status === 'fulfilled') {
                    // Extract the data from the resolved promise
                    const response = results[0].value;
                    if (response.ok) {
                        
                        // Parse the JSON data from the response
                        const response_data = await response.json();
                        // populateOpenOpenOrdersTable(response_data.data);
                        populateOpenOrders();
                    } else {
                        console.error('Error fetching orders:', response.statusText);
                    }
                } else {
                    console.error('Request failed:', results[0].reason);
                }
        }
    } 
    else {
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
async function get_tpsl_info_promise(ordId, ccy) {
    const token = getAuthToken();
    const username = localStorage.getItem('username');
    const redis_key = localStorage.getItem('key');

    if (!token || !username || !redis_key) {
        alert("You must be logged in to access this.");
        return;
    }

    const request_data = { "username": username, "redis_key": redis_key, 'ordId': ordId, 'ccy': ccy };

    // Fetch request
    const thirdOrderPromise = fetch(`http://${hostname}:6061/htx/swap/get_tpsl_info`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request_data)
    });

    // Wait for the response
    const response = await thirdOrderPromise;

    // Check if the response is successful
    if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
    }

    // Parse the response body as JSON
    const tpsl_info_promise = await response.json();

    // Log the data to the console

    return tpsl_info_promise;
}

async function get_tpsl_info(ordId,instId) {
    const tpsl_info = await get_tpsl_info_promise(ordId,instId);
    return tpsl_info
}


async function Htx2OkxFormatOrders(responseData) {
    // Extract orders from the response
    const { orders } = responseData;
    // console.log('respionseDta',responseData)
    console.log('response_data',responseData)
    const transformedOrders = []
    for (const row of responseData.orders) {
        console.log('row', row);
        try {
            let contract_code = row.contract_code
            let is_tpsl = row.is_tpsl
            let order_id = row.order_id_str
            let sl_price = '';
            let tp_price = '';
            let tp_algo_id = ''
            let sl_algo_id = ''
            let algoOrds = []
            console.log(is_tpsl)
            if (is_tpsl){
                const tpsl_info = await get_tpsl_info(order_id, contract_code);
                console.log('tpsl_info', tpsl_info);
                
                algoOrds.push({
                    "amendPxOnTriggerType": "0",
                    "attachAlgoClOrdId": "",
                    "attachAlgoId": [],
                    "failCode": "",
                    "failReason": "",
                    "slOrdPx": "-1",
                    "slTriggerPx": "90",
                    "slTriggerPxType": "last",
                    "sz": "",
                    "tpOrdKind": "limit",
                    "tpOrdPx": "99999",
                    "tpTriggerPx": "",
                    "tpTriggerPxType": ""
                  })
                tpsl_info.tpsl_order_info.forEach(order => {
                    algoOrds[0]["sz"] = order.volume
                    if (order.tpsl_order_type === 'sl') {
                        sl_price = order.trigger_price;
                        sl_algo_id = order.relation_tpsl_order_id
                        algoOrds[0]["attachAlgoId"].push(sl_algo_id)
                        algoOrds[0]["slTriggerPx"] = sl_price
            
                    } else if (order.tpsl_order_type === 'tp') {
                        tp_price = order.trigger_price;
                        tp_algo_id = order.relation_tpsl_order_id
                        algoOrds[0]["attachAlgoId"].push(tp_algo_id)
                        algoOrds[0]["tpOrdPx"] = tp_price
                    }
                });
                console.log("SL Price:", sl_price);
                console.log("TP Price:", tp_price);
                
            }

            let transformedRow = {
                accFillSz: row.trade_volume.toString(),
                algoClOrdId: "",
                algoId: sl_algo_id && !tp_algo_id ? [] :[sl_algo_id,tp_algo_id],
                attachAlgoClOrdId: "",
                attachAlgoOrds:sl_algo_id && !tp_algo_id ? [] :algoOrds ,
                avgPx: row.trade_avg_price ? row.trade_avg_price.toString() : "",
                cTime: row.created_at.toString(),
                cancelSource: row.canceled_source || "",
                cancelSourceReason: "",
                category: "normal",
                ccy: "",
                clOrdId: row.client_order_id || "",
                fee: row.fee.toString(),
                feeCcy: row.fee_asset,
                fillPx: "",
                fillSz: row.trade_volume.toString(),
                fillTime: "",
                instId: `${row.contract_code}-SWAP`,
                instType: "SWAP",
                isTpLimit: row.is_tpsl ? "true" : "false",
                lever: row.lever_rate.toString(),
                linkedAlgoOrd: sl_algo_id && !tp_algo_id ? '' : { algoId: [sl_algo_id, tp_algo_id] },
                ordId: row.order_id_str,
                ordType: row.order_price_type,
                pnl: row.profit.toString(),
                posSide: "net",
                px: row.price.toString(),
                pxType: "",
                pxUsd: "",
                pxVol: "",
                quickMgnType: "",
                rebate: "0",
                rebateCcy: row.fee_asset,
                reduceOnly: "false",
                side: row.direction,
                slOrdPx: "",
                slTriggerPx: sl_price|| "",
                slTriggerPxType: "",
                source: row.order_source || "",
                state: mapStatusToState(row.status),
                stpId: "",
                stpMode: "cancel_maker",
                sz: row.volume.toString(),
                tag: "",
                tdMode: "isolated", // Assuming isolated margin; adjust if needed
                tgtCcy: "",
                tpOrdPx: "",
                tpTriggerPx: tp_price.toString() || "",
                tpTriggerPxType: "",
                tradeId: "",
                uTime: row.update_time.toString(),
            }

            transformedOrders.push(transformedRow)
            
        } catch (error) {
            console.error('Error fetching TPSL info:', error);
        }
    }
    
    
    
    
    // Output the results
    // console.log("SL Price:", sl_price);
    // console.log("TP Price:", tp_price);
    
    // Transform each order to match the desired OKX format
    // const transformedOrders = orders.map(order => ({
    //     accFillSz: order.trade_volume.toString(),
    //     algoClOrdId: "",
    //     algoId: [sl_algo_id,tp_algo_id] || [],
    //     attachAlgoClOrdId: "",
    //     attachAlgoOrds: algoOrds | [],
    //     avgPx: order.trade_avg_price ? order.trade_avg_price.toString() : "",
    //     cTime: order.created_at.toString(),
    //     cancelSource: order.canceled_source || "",
    //     cancelSourceReason: "",
    //     category: "normal",
    //     ccy: "",
    //     clOrdId: order.client_order_id || "",
    //     fee: order.fee.toString(),
    //     feeCcy: order.fee_asset,
    //     fillPx: "",
    //     fillSz: order.trade_volume.toString(),
    //     fillTime: "",
    //     instId: `${order.contract_code}-SWAP`,
    //     instType: "SWAP",
    //     isTpLimit: order.is_tpsl ? "true" : "false",
    //     lever: order.lever_rate.toString(),
    //     linkedAlgoOrd: { algoId: [sl_algo_id,tp_algo_id] },
    //     ordId: order.order_id_str,
    //     ordType: order.order_price_type,
    //     pnl: order.profit.toString(),
    //     posSide: "net",
    //     px: order.price.toString(),
    //     pxType: "",
    //     pxUsd: "",
    //     pxVol: "",
    //     quickMgnType: "",
    //     rebate: "0",
    //     rebateCcy: order.fee_asset,
    //     reduceOnly: "false",
    //     side: order.direction,
    //     slOrdPx: "",
    //     slTriggerPx: sl_price|| "",
    //     slTriggerPxType: "",
    //     source: order.order_source || "",
    //     state: mapStatusToState(order.status),
    //     stpId: "",
    //     stpMode: "cancel_maker",
    //     sz: order.volume.toString(),
    //     tag: "",
    //     tdMode: "isolated", // Assuming isolated margin; adjust if needed
    //     tgtCcy: "",
    //     tpOrdPx: "",
    //     tpTriggerPx: tp_price.toString() || "",
    //     tpTriggerPxType: "",
    //     tradeId: "",
    //     uTime: order.update_time.toString(),
    // }));

    // {'status': ['ok', 'no error'], 'data': {'symbol': 'BTC', 'contract_code': 'BTC-USD', 'volume': 1, 'price': 60000, 'order_price_type': 'limit', 'direction': 'buy', 'offset': 'open', 'lever_rate': 5, 'order_id': 1313907123482300416, 'order_id_str': '1313907123482300416', 'client_order_id': None, 'created_at': 1733301469441, 'trade_volume': 0, 'trade_turnover': 0, 'fee': 0, 'trade_avg_price': None, 'margin_frozen': 0.000333333333333333, 'profit': 0, 'status': 3, 'order_type': 1, 'order_source': 'web', 'fee_asset': 'BTC', 'canceled_at': 0, 'tpsl_order_info': [{'volume': 1.0, 'direction': 'sell', 'tpsl_order_type': 'tp', 'order_id': 1313907123482300417, 'order_id_str': '1313907123482300417', 'trigger_type': 'ge', 'trigger_price': 100000.0, 'order_price': 100000.0, 'created_at': 1733301469452, 'order_price_type': 'limit', 'relation_tpsl_order_id': '1313907123482300418', 'status': 1, 'canceled_at': 0, 'fail_code': None, 'fail_reason': None, 'triggered_price': None, 'relation_order_id': '-1'}, {'volume': 1.0, 'direction': 'sell', 'tpsl_order_type': 'sl', 'order_id': 1313907123482300418, 'order_id_str': '1313907123482300418', 'trigger_type': 'le', 'trigger_price': 20000.0, 'order_price': 20000.0, 'created_at': 1733301469452, 'order_price_type': 'limit', 'relation_tpsl_order_id': '1313907123482300417', 'status': 1, 'canceled_at': 0, 'fail_code': None, 'fail_reason': None, 'triggered_price': None, 'relation_order_id': '-1'}], 'sMsg': 'Orders placed'}, 'ts': 1733301592504, 'sCode': 200}

    // Wrap in the final response structure
    return transformedOrders
}

// Helper function to map HTX status codes to OKX state strings
function mapStatusToState(status) {
    const statusMap = {
        3: "live",      // Example: live order
        4: "cancelled", // Example: cancelled order
        // Add additional mappings if needed
    };
    return statusMap[status] || "unknown"; // Default to "unknown" if status is not mapped
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

