

function addNewRow() {
    const algoList = document.getElementById('algo-list');

    // Check if a new row already exists
    if (document.getElementById('new-row')) {
        alert('You can only add one new row at a time.');
        return;
    }

    // Create a new table row with a unique ID
    const newRow = document.createElement('tr');
    newRow.id = 'new-row'; // Unique identifier for the new row
    newRow.innerHTML = `
        <td>
            <input type="text" class="form-control" placeholder="Algo Name" id="new-algo-name">
        </td>
        <td>
            <select class="form-control" id="new-lead-exchange">
                <option value="okx">okx</option>
                <option value="htx">htx</option>
            </select>
        </td>
        <td>
            <select class="form-control" id="new-lag-exchange">
                <option value="okx">okx</option>
                <option value="htx">htx</option>
            </select>
        </td>
        <td>
            <input type="number" class="form-control" placeholder="Spread" id="new-spread">
        </td>
        <td>
            <input type="number" class="form-control" placeholder="Qty" id="new-qty" >
        </td>
       <td>
            <input type="text" class="form-control" placeholder="Ccy" id="new-ccy" required title="Please enter a value for Ccy.">
        </td>

        <td>
            <span class="badge bg-secondary">New</span>
        </td>
        <td>
            <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" id="new-status" >
            </div>
        </td>
        <td class="flex justify-content-between align-items-center">
            <button class="btn btn-success btn-sm flex-grow-1 me-1" style="min-width: 80px;" onclick="saveRow(this)">Save</button>
            <button class="btn btn-danger btn-sm flex-grow-1" style="min-width: 80px;" onclick="deleteActionRow(this)" >Delete</button>
        </td>
    `;

    // Append the new row to the table
    algoList.appendChild(newRow);
}

// Function to delete a row, including the new row
function deleteActionRow(button) {
    const row = button.closest('tr');
    row.remove();
}


function deleteRow(button) {
    deleteAlgo(username,algoname)

    const row = button.parentElement.parentElement; // Get the row containing the button
    row.remove(); // Remove the row from the table
}

function saveRow(){
    const ccyInput = document.querySelector('#new-ccy');

    // Check if the "Ccy" input is empty
    if (!ccyInput.value.trim()) {
        // If the "Ccy" field is empty, show a custom message and add a red border to the input field
        ccyInput.setCustomValidity('Please enter a value for Ccy.');
        ccyInput.reportValidity(); // This will show the validity message
        return; // Prevent saving if the field is invalid
    } else {
        // If the input is valid, proceed to save the row
        ccyInput.setCustomValidity(''); // Reset any previous validation messages

        // Implement your save logic here (e.g., send the data to the server or add the row to the table)
        console.log('Row saved');
        // For example, you can replace "New" badge with a "Saved" status or submit the data
    }
    
    username= localStorage.getItem('username')
    algo_name= document.getElementById('new-algo-name').value
    lead_exchange= document.getElementById('new-lead-exchange').value
    lag_exchange= document.getElementById('new-lag-exchange').value
    spread=document.getElementById('new-spread').value
    qty=document.getElementById('new-qty').value
    ccy=document.getElementById('new-ccy').value
    state=document.getElementById('new-status').checked
    console.log(username, algo_name,lead_exchange, lag_exchange, spread, qty, ccy, state)
    addAlgo(username, algo_name,lead_exchange, lag_exchange, spread, qty, ccy, state)
    // fetchAlgoData()
}

function addAlgo(username, algo_name,lead_exchange, lag_exchange, spread, qty, ccy, state){
    const requestBody = {
        lead_exchange: lead_exchange,
        lag_exchange: lag_exchange,
        spread: spread,
        qty: qty,
        ccy: ccy,
        state:state,
        username: username,
        algo_name: algo_name,
    };
    
    fetch("http://localhost:5020/db/add_algo", {
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
    console.log(username,algoname)
    const requestBody = {
        username: username,
        algo_name: algoname
    };
    
    fetch("http://localhost:5020/db/delete_algo", {
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
    console.log(username)
    fetch(`http://127.0.0.1:5020/db/get_algo_list?username=${username}`)
        .then(response => response.json())
        .then(data => {
            const algoList = document.getElementById('algo-list');
            algoList.innerHTML = ''; // Clear existing rows

            data.forEach((algo_arr, index) => {
                const algo = algo_arr[0];
                const newRow = document.createElement('tr');
                const isRunning = algo.state;
                const algoName = algo.algo_name
                console.log(algo_arr)
                newRow.innerHTML = `
                    <td>${algo['algo_name']}</td>
                    <td>
                        <select class="form-control editable-field" id="input-${algoName}-leading-exchange">
                            <option value="okx" ${algo.lead_exchange === 'okx' ? 'selected' : ''}>okx</option>
                            <option value="htx" ${algo.lead_exchange === 'htx' ? 'selected' : ''}>htx</option>
                        </select>
                    </td>
                    <td>
                        <select class="form-control editable-field" id="input-${algoName}-lagging-exchange">
                            <option value="okx" ${algo.lag_exchange === 'okx' ? 'selected' : ''}>okx</option>
                            <option value="htx" ${algo.lag_exchange === 'htx' ? 'selected' : ''}>htx</option>
                        </select>
                    </td>
                    <td>
                        <input type="text" class="form-control editable-field" id="input-${algoName}-spread" placeholder="Spread" value="${algo.spread}">
                    </td>
                    <td>
                        <input type="text" class="form-control editable-field" id="input-${algoName}-qty" placeholder="Quantity" value="${algo.qty}">
                    </td>
                    <td>
                        <input type="text" class="form-control editable-field" id="input-${algoName}-ccy" placeholder="Currency" value="${algo.ccy}">
                    </td>
                    <td>
                        <span id="status-algo${algoName}" class="badge ${isRunning ? 'bg-success' : 'bg-secondary'}">
                            ${isRunning ? 'Running' : 'Stopped'}
                        </span>
                    </td>
                    <td>
                        <div class="form-check form-switch ">
                            <input class="form-check-input" type="checkbox" id="flexSwitchCheckDiaoyu-${algoName}" ${isRunning ? 'checked' : ''} 
                            onclick="handleAlgoToggle(this, '${algoName}','${algoName}' , 'status-algo${algoName}')">
                        </div>
                    </td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="deleteAlgo('${username}','${algoName}')">Delete</button>
                    </td>
                `;

                algoList.appendChild(newRow);

                // Add event listeners for all inputs and selects in the row
                const editableFields = newRow.querySelectorAll('.editable-field');
                editableFields.forEach(field => {
                    const originalValue = field.value || field.selectedOptions[0]?.value;

                    field.addEventListener('change', (event) => {
                        // Highlight the field with a red border
                        field.style.border = '2px solid red';
                        console.log(event)
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
            const saveAllButton = document.getElementById('save-all-button');
            if (!saveAllButton) {
                const newButton = document.createElement('button');
                newButton.id = 'save-all-button';
                newButton.textContent = 'Save All Changes';
                newButton.className = 'btn btn-primary mt-3';
                newButton.addEventListener('click', () => saveAllChanges());
                document.body.appendChild(newButton);
            }
        })
        .catch(error => {
            console.error('Error fetching algo data:', error);
        });
}


// Call the function to fetch data and populate the table when the page loads
document.addEventListener('DOMContentLoaded', fetchAlgoData);




// Handle the toggle change
function handleAlgoToggle(checkbox, algo_name, algo, statusId) {
    console.log('fetchiong along')
    //update db to stop algo
    // console.log(checkbox.checked, algo_name, algo, statusId)
    username = localStorage.getItem('username')
    jwt_token = localStorage.getItem('jwt_token')
    key = localStorage.getItem('key')
    // getting new fields
    lead_exchange = document.getElementById(`input-${algo_name}-leading-exchange`).value
    lag_exchange = document.getElementById(`input-${algo_name}-lagging-exchange`).value
    spread = document.getElementById(`input-${algo_name}-spread`).value
    qty = document.getElementById(`input-${algo_name}-qty`).value
    ccy = document.getElementById(`input-${algo_name}-ccy`).value
    // status = document.getElementById(`input-${algo_name}-status`).value
    // checkbox = state


    // lead_exchange, lag_exchange, spread, qty, ccy , state,username, algo_name
    


    console.log(lead_exchange,lag_exchange,spread,qty,ccy,checkbox.checked,username,algo_name)
    // Step1: update database by modifying - required input: username and algo_name
    const requestBody = {
        lead_exchange: lead_exchange,
        lag_exchange: lag_exchange,
        spread: spread,
        qty: qty,
        ccy: ccy,
        state: checkbox.checked,
        username: username,
        algo_name: algo_name,
    };
    
    fetch("http://localhost:5020/db/modify_status", {
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
            // Handle successful response here
        })
        .catch(error => {
            console.error("Error sending POST request:", error);
        });
      

    // Step2: Switch on strat with subproces



    

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