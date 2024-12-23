

// Function to add a new row to the DB and update the frontend
function addNewRow() {
    const data = {
        leadingExchange: "okx",  // Default or user-selected
        laggingExchange: "htx",  // Default or user-selected
        param1: "default",       // Default or user-entered value
        param2: "default",       // Default or user-entered value
        param3: "default"        // Default or user-entered value
    };

    // Send the data to the server to add to the database
    fetch('/add_algo', {  // Change '/add_algo' to your server's endpoint for adding data
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // If the row was added successfully, refresh the table
            fetchAlgoData();  // Refresh table with new data from the DB
        }
    })
    .catch(error => {
        console.error('Error adding new row:', error);
    });
}
function fetchAlgoData() {
    fetch('http://127.0.0.1:5020/db/get_algo_list')
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
                        <input type="text" class="form-control editable-field" id="input-${algoName}-spread" placeholder="Quantity" value="${algo.qty}">
                    </td>
                    <td>
                        <input type="text" class="form-control editable-field" id="input-${algoName}-qty" placeholder="Spread" value="${algo.spread}">
                    </td>
                    <td>
                        <input type="text" class="form-control editable-field" id="input-${algoName}-ccy" placeholder="Currency" value="${algo.ccy}">
                    </td>
                    <td>
                        <span id="status-algo${algoName}" class="badge ${isRunning ? 'bg-success' : 'bg-secondary'}">
                            ${isRunning ? 'Running' : 'Idle'}
                        </span>
                    </td>
                    <td>
                        <div class="form-check form-switch ">
                            <input class="form-check-input" type="checkbox" id="flexSwitchCheckDiaoyu-${algoName}" ${isRunning ? 'checked' : ''} 
                            onclick="handleAlgoToggle(this, '${algoName}','${algo.algo_name}' , 'status-algo${algoName}')">
                        </div>
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
        statusBadge.textContent = `Idle`;
        statusBadge.classList.remove('bg-success');
        statusBadge.classList.add('bg-secondary');
    }
}