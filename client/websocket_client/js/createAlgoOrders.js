


// Function to open the modal
function openAlgoModal() {
    const modal = document.getElementById('algoModal');
    modal.style.display = 'block';
}

// Function to close the modal
function closeAlgoModal() {
    const modal = document.getElementById('algoModal');
    modal.style.display = 'none';
    // document.getElementById('algoForm').reset(); // Reset form fields
}

// Function to save the algo details
function saveAlgo() {
    const algoType = document.getElementById('new-algo-type').value;
    const algoName = document.getElementById('new-algo-name').value;
    const leadExchange = document.getElementById('new-algo-lead-exchange').value;
    const lagExchange = document.getElementById('new-algo-lag-exchange').value;
    const ccy = document.getElementById('new-algo-ccy').value;
    const spread = document.getElementById('new-algo-spread').value;
    const quantity = document.getElementById('new-algo-quantity').value;
    const instrument = document.getElementById('new-algo-instrument').value;
    const contractType = document.getElementById('new-algo-contract-type').value;
    const status = document.getElementById('new-algo-status').checked ? 'Active' : 'Inactive';
    const status_bool = document.getElementById('new-algo-status').checked 
    
    if (!algoName || !spread || !quantity) {
        alert('Please fill in all required fields.');
        return;
    }

    if (leadExchange == lagExchange){
        alert('Please select a different lead and lag exchange')
        return;
    }

    const algoList_temp = document.getElementById('algo-list-new');
    const algoList = document.getElementById('algo-list')
    const newRow = document.createElement('tr');
    newRow.innerHTML = `
       <td >${algoType}-${algoName}</td>
        <td>
            <div>
                <span>${leadExchange}</span><br />
                <span>${lagExchange}</span>
            </div>
        </td>
        <td>${spread} - ${quantity}</td>
       
        <td>${ccy}</td>
        
        <td>
            ${instrument} (${contractType})
        </td>
       
        <td>
            <span class="badge bg-warning">New Order</span>
        </td>
        <td>
            <span class="badge ${status === 'Active' ? 'bg-success' : 'bg-danger'}">
                ${status}
            </span>
        </td>
        
        <td>
            <div class="d-flex justify-content-around">
                <button class="btn btn-success btn-sm me-1" onclick="saveNewAlgoRow(this)">
                    <i class="bi bi-check-lg"></i> Save
                </button>
                <button class="btn btn-danger btn-sm" onclick="deleteNewRow(this)">
                    <i class="bi bi-trash"></i> Delete
                </button>
            </div>
        </td>

    `;
    algoList_temp.appendChild(newRow);

    closeAlgoModal(); // Close modal after saving
}

// Function to delete a row
function deleteNewRow(button) {
    const row = button.closest('tr');
    row.remove();
}



function deleteRow(button) {
    deleteAlgo(username,algoname)

    const row = button.parentElement.parentElement; // Get the row containing the button
    row.remove(); // Remove the row from the table.

}



function saveNewAlgoRow(button){
    // console.log('newalgodata')
    // const ccyInput = document.querySelector('#new-ccy');
    username= localStorage.getItem('username')
   
    const algoType = document.getElementById('new-algo-type').value;
    const algoName = document.getElementById('new-algo-name').value;
    const leadExchange = document.getElementById('new-algo-lead-exchange').value;
    const lagExchange = document.getElementById('new-algo-lag-exchange').value;
    const spread = document.getElementById('new-algo-spread').value;
    const quantity = document.getElementById('new-algo-quantity').value;
    const ccy = document.getElementById('new-algo-ccy').value;
    const instrument = document.getElementById('new-algo-instrument').value;
    const contractType = document.getElementById('new-algo-contract-type').value;
    const state = document.getElementById('new-algo-status').checked 
    
    addAlgo(username,algoType, algoName,leadExchange, lagExchange, spread, quantity, ccy,instrument,contractType, state)
    // fetchAlgoData()
    const row = button.closest('tr');
    // Remove the row from the table
    row.remove();
}


function addAlgo(username,algoType, algoName,leadExchange, lagExchange, spread, quantity, ccy,instrument,contractType, state){
    const requestBody = {
        username: username,
        algo_type:algoType,
        algo_name: algoName,
        lead_exchange: leadExchange,
        lag_exchange: lagExchange,
        spread: spread,
        qty: quantity,
        ccy: ccy,
        instrument:instrument,
        contract_type:contractType,
        state:state
    };
    
    fetch(`http://${hostname}:5020/db/add_algo`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            fetchAlgoData()
            return response.json();
        })
        .then(data => {
            console.log("Success:", data);
            // Handle successful response here
        })
        .catch(error => {
            alert(`Error sending request (DB Error):${error}`)
            console.error("Error sending POST request:", error);
            return
        });
}

function deleteAlgo(username,algoname){
    // console.log(username,algoname)
    const requestBody = {
        username: username,
        algo_name: algoname
    };
    
    fetch(`http://${hostname}:5020/db/delete_algo`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            fetchAlgoData()
            return response.json();
        })
        .then(data => {
            console.log("Success:", data);
            // Handle successful response here
        })
        .catch(error => {
            alert(`Error sending request (DB Error):${error}`)
            console.error("Error sending POST request:", error);
            return
        });
}

function fetchAlgoData() {
    const username = localStorage.getItem('username');
    fetch(`http://${hostname}:5020/db/get_algo_list?username=${username}`)
        .then(response => response.json())
        .then(data => {
            const algoList = document.getElementById('algo-list');
            algoList.innerHTML = ''; // Clear existing rows
            
            data.forEach((algo_arr, index) => {
                const algo = algo_arr[0];
                
                const newRow = document.createElement('tr');
                const isRunning = algo.state;
                const algoName = algo.algo_name
                const algoType = algo.algo_type
                var contractType = algo.contract_type
                var instrument = algo.instrument
                var color = null
                if (algoType == 'diaoyu')
                {   
                    badgeColor = 'bg-primary'
                }
                else if (algoType == 'diaoxia'){
                    badgeColor = 'bg-danger'
                }
                
                newRow.innerHTML = `

                    <td >
                        <div class="badge ${badgeColor}">
                            ${algoType}
                        </div>
                        <div class="text-muted">
                            ${algoName}
                        </div>
                    </td>

                    <td>
                        <div>
                            <select class="form-control editable-field" id="input-${algoName}-leading-exchange" disabled>
                                <option value="okx" ${algo.lead_exchange === 'okx' ? 'selected' : ''}>okx</option>
                                <option value="htx" ${algo.lead_exchange === 'htx' ? 'selected' : ''}>htx</option>
                            </select>
                        </div>
                        <div>
                            <select class="form-control editable-field" id="input-${algoName}-lagging-exchange" disabled>
                                <option value="okx" ${algo.lag_exchange === 'okx' ? 'selected' : ''}>okx</option>
                                <option value="htx" ${algo.lag_exchange === 'htx' ? 'selected' : ''}>htx</option>
                            </select>
                        </div>
                        
                    </td>
                    
                    <td>
                        <div>
                            <input type="text" class="form-control editable-field" id="input-${algoName}-spread" placeholder="Spread" value="${algo.spread}" disabled>
                        </div>
                        <div>
                            <input type="text" class="form-control editable-field" id="input-${algoName}-qty" placeholder="Quantity" value="${algo.qty}" disabled>
                        </div>

                    </td>
                   
                   
                    <td>
                        <select class="form-control editable-field" 
                            id="input-${algoName}-ccy" disabled>
                        <option value="" >Select Currency Pair</option>
                        ${instrument === 'futures' 
                            ? `
                                <option value="BTC" ${algo.ccy === "BTC" ? "selected" : ""}>BTC</option>
                            `
                            : `
                                <option value="BTC-USD-SWAP" ${algo.ccy === "BTC-USD-SWAP" ? "selected" : ""}>BTC-USD-SWAP</option>
                            `
                        }
                    </select>

                    </td>
                    <td>
                        <div>
                            <select class="form-control editable-field" 
                                    id="input-${algoName}-instrument" 
                                    onchange="updateCurrencyOptionsGeneral('input-${algoName}-instrument', 'input-${algoName}-ccy', 'input-${algoName}-contract-type-container')" disabled>
                                <option value="swap" ${instrument === 'swap' ? 'selected' : ''}>Swap</option>
                                <option value="futures" ${instrument === 'futures' ? 'selected' : ''}>Futures</option>
                            </select>
                        </div>
                        <div id="input-${algoName}-contract-type-container" 
                            style="display: ${instrument === 'futures' ? 'block' : 'none'};">
                            <select class="form-control editable-field" 
                                    id="input-${algoName}-contract-type" disabled>
                                <option value="">Select Contract Type</option>
                                <option value="thisweek" ${contractType === 'thisweek' ? 'selected' : ''}>This Week</option>
                                <option value="nextweek" ${contractType === 'nextweek' ? 'selected' : ''}>Next Week</option>
                                <option value="quarter" ${contractType === 'quarter' ? 'selected' : ''}>Quarter</option>
                            </select>
                        </div>

                    </td>

                   
                    <td>
                        <span id="status-algo-${algoName}" class="badge ${isRunning ? 'bg-success' : 'bg-secondary'}">
                            ${isRunning ? 'Running' : 'Stopped'}
                        </span>
                    </td>
                    
                    <td>
                        <div class="form-check form-switch ">
                            <input class="form-check-input" type="checkbox" id="${algoType}-${algoName}" ${isRunning ? 'checked' : ''} 
                            onclick="handleAlgoToggle(this, '${algoName}','${algoType}','status-algo-${algoName}')">
                        </div>
                    </td>
                    <td>
                        <button class="btn btn-danger justify-content-around" onclick="deleteAlgo('${username}','${algoName}')"><i class="bi bi-trash"></i> Delete</button>
                    </td>
                `;


                algoList.appendChild(newRow);

                // Add event listeners for all inputs and selects in the row
                const editableFields = newRow.querySelectorAll('.editable-field');
                editableFields.forEach(field => {
                    // const originalValue = field.value || field.selectedOptions[0]?.value;
                    
                    field.addEventListener('change', (event) => {
                        // Highlight the field with a red border
                        field.style.border = '2px solid red';
                        // console.log(event)
                        // Add a confirmation UI (cross and tick buttons)
                        if (!field.nextElementSibling) {
                            const confirmWrapper = document.createElement('div');
                            confirmWrapper.style.display = 'inline-block';
                            confirmWrapper.style.marginLeft = '5px';

                            // Tick button
                            const tickButton = document.createElement('button');
                            tickButton.textContent = '✔';
                            tickButton.style.color = 'green';
                            tickButton.style.marginRight = '5px';
                            tickButton.addEventListener('click', () => {
                                field.style.border = ''; // Remove red border
                                field.dataset.edited = true; // Mark field as confirmed
                                confirmWrapper.remove(); // Remove the buttons
                                jwt_token = localStorage.getItem('jwt_token')
                                key = localStorage.getItem('key')
                                // getting new fields
                                lead_exchange = document.getElementById(`input-${algoName}-leading-exchange`).value
                                lag_exchange = document.getElementById(`input-${algoName}-lagging-exchange`).value
                                spread = document.getElementById(`input-${algoName}-spread`).value
                                qty = document.getElementById(`input-${algoName}-qty`).value
                                ccy = document.getElementById(`input-${algoName}-ccy`).value
                                state = document.getElementById(`${algoType}-${algoName}`).checked
                                instrument = document.getElementById(`input-${algoName}-instrument`).value
                                contractType = document.getElementById(`input-${algoName}-contract-type`).value
                            
                                // username,algoType, algoName,leadExchange, lagExchange, spread, quantity, ccy,instrument,contractType, state
                                modifyAlgo(username,algoType, algoName,lead_exchange, lag_exchange, spread, qty, ccy,instrument,contractType,state)
                            });

                            // Cross button
                            const crossButton = document.createElement('button');
                            crossButton.textContent = '✖';
                            crossButton.style.color = 'red';
                            crossButton.addEventListener('click', () => {
                                field.value = originalValue; // Revert to original value
                                field.style.border = ''; // Remove red border
                                confirmWrapper.remove(); // Remove the buttons
                            });

                            confirmWrapper.appendChild(tickButton);
                            confirmWrapper.appendChild(crossButton);
                            field.parentNode.appendChild(confirmWrapper);
                        }
                    });
                });
            });

            // Add a "Save All Changes" button
            // const saveAllButton = document.getElementById('save-all-button');
            // if (!saveAllButton) {
            //     const newButton = document.createElement('button');
            //     newButton.id = 'save-all-button';
            //     newButton.textContent = 'Save All Changes';
            //     newButton.className = 'btn btn-primary mt-3';
            //     newButton.addEventListener('click', () => saveAllChanges());
            //     document.body.appendChild(newButton);
            // }
        })
        .catch(error => {
            console.error('Error fetching algo data:', error);
        });
}

// Call the function to fetch data and populate the table when the page loads
document.addEventListener('DOMContentLoaded', fetchAlgoData);


function modifyAlgo(username,algoType, algoName,lead_exchange, lag_exchange, spread, quantity, ccy,instrument,contractType, state){
    
    const requestBody = {
        username: username,
        algo_type:algoType,
        algo_name:algoName,
        lead_exchange: lead_exchange,
        lag_exchange: lag_exchange,
        spread: spread,
        qty: quantity,
        ccy: ccy,
        instrument:instrument,
        contract_type:contractType,
        state: state,
    };
   
    fetch(`http://${hostname}:5020/db/modify_algo`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Success:", data);
            fetchAlgoData()

            // Handle successful response here
        })
        .catch(error => {
            
            console.error("Error sending POST request:", error);
        });
}

// Handle the toggle change
function handleAlgoToggle(checkbox, algo_name,algo_type,statusId) {
    console.log('fetching along',checkbox,algo_name,algo_type)
    //update db to stop algo
    username = localStorage.getItem('username')
    jwt_token = localStorage.getItem('jwt_token')
    key = localStorage.getItem('key')
    // getting new fields
    lead_exchange = document.getElementById(`input-${algo_name}-leading-exchange`).value
    lag_exchange = document.getElementById(`input-${algo_name}-lagging-exchange`).value
    
    spread = document.getElementById(`input-${algo_name}-spread`).value
    quantity = document.getElementById(`input-${algo_name}-qty`).value

    ccy = document.getElementById(`input-${algo_name}-ccy`).value
    amended_instrument = document.getElementById(`input-${algo_name}-instrument`).value
    contractType = document.getElementById(`input-${algo_name}-contract-type`).value
    state = checkbox.checked
   
    modifyAlgo(username,algo_type, algo_name,lead_exchange, lag_exchange, spread, quantity, ccy,instrument,contractType, state)


    const statusBadge = document.getElementById(statusId);
    if (checkbox.checked) {
        statusBadge.textContent = `Running`;
        statusBadge.classList.remove('bg-secondary');
        statusBadge.classList.add('bg-success');
    } else {
        statusBadge.textContent = `Stopped`;
        statusBadge.classList.remove('bg-success');
        statusBadge.classList.add('bg-secondary');
    }
}


// create a listener to listen for notification of db updates. if there is an update in db, it should fetch data from the database again.


// // // Set up the scheduler
function startAlgoOrderDetailsFetchScheduler(interval = 5000) {
    // Call getTradeHistory immediately
    fetchAlgoData();

    // Schedule getTradeHistory to run every few seconds
    setInterval(fetchAlgoData, interval);
}

// Start the scheduler when the page loads
document.addEventListener('DOMContentLoaded', () => {
    startAlgoOrderDetailsFetchScheduler();
});
