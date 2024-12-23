// // Function to add a new row to the table
// function addNewRow() {

//     const algoList = document.getElementById('algo-list');

//     // Create a new row
//     const newRow = document.createElement('tr');

//     // Create cells and append the right elements
//     newRow.innerHTML = `
//         <td>Algo ${algoList.children.length + 1}</td>
//         <td>
//             <select class="form-control" id="input-algo-${algoList.children.length + 1}-leading-exchange">
//                 <option value="okx" selected>okx</option>
//                 <option value="htx">htx</option>
//             </select>
//         </td>
//         <td>
//             <select class="form-control" id="input-${algoList.children.length + 1}-lagging-exchange">
//                 <option value="okx">okx</option>
//                 <option value="htx" selected>htx</option>
//             </select>
//         </td>
//         <td>
//             <input type="text" class="form-control" id="input-${algoList.children.length + 1}-param-1" placeholder="Text" value="default">
//         </td>
//         <td>
//             <input type="text" class="form-control" id="input-${algoList.children.length + 1}-param-2" placeholder="Text" value="default">
//         </td>
//         <td>
//             <input type="text" class="form-control" id="input-${algoList.children.length + 1}-param-3" placeholder="Text" value="default">
//         </td>
//         <td>
//             <span id="status-algo${algoList.children.length + 1}" class="badge bg-secondary">Idle</span>
//         </td>
//         <td>
//             <div class="form-check form-switch ">
//                 <input class="form-check-input" type="checkbox" id="flexSwitchCheckDiaoyu-${algoList.children.length + 1}" onclick="handleAlgoToggle(this, 'Algo ${algoList.children.length + 1}', 'input-${algoList.children.length + 1}-param-1', 'input-${algoList.children.length + 1}-param-2', 'status-algo${algoList.children.length + 1}')">
//             </div>
//         </td>
//     `;

//     // Append the new row to the tbody
//     algoList.appendChild(newRow);
// }

// // Example of handling row toggle (this could be further defined based on your needs)
// function handleAlgoToggle(checkbox, algoName, input1, input2, statusId) {
//     const statusBadge = document.getElementById(statusId);
//     if (checkbox.checked) {
//         statusBadge.textContent = `${algoName} Active`;
//         statusBadge.classList.remove('bg-secondary');
//         statusBadge.classList.add('bg-success');
//     } else {
//         statusBadge.textContent = `${algoName} Idle`;
//         statusBadge.classList.remove('bg-success');
//         statusBadge.classList.add('bg-secondary');
//     }
// }

// // Call addNewRow() to add a new row when needed (e.g., on a button click)




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

// Function to fetch data from the server and populate the table
function fetchAlgoData() {
    fetch('http://127.0.0.1:5060/db/get_algo_list')  // Change '/get_algos' to your server's endpoint for fetching data
        .then(response => response.json())
        .then(data => {
            const algoList = document.getElementById('algo-list');
            algoList.innerHTML = '';  // Clear existing rows

            // Populate table with data from the server
            data.forEach((algo, index) => {
                const newRow = document.createElement('tr');
                newRow.innerHTML = `
                    <td>Algo ${index + 1}</td>
                    <td>
                        <select class="form-control" id="input-algo-${index + 1}-leading-exchange">
                            <option value="okx" ${algo.leadingExchange === 'okx' ? 'selected' : ''}>okx</option>
                            <option value="htx" ${algo.leadingExchange === 'htx' ? 'selected' : ''}>htx</option>
                        </select>
                    </td>
                    <td>
                        <select class="form-control" id="input-${index + 1}-lagging-exchange">
                            <option value="okx" ${algo.laggingExchange === 'okx' ? 'selected' : ''}>okx</option>
                            <option value="htx" ${algo.laggingExchange === 'htx' ? 'selected' : ''}>htx</option>
                        </select>
                    </td>
                    <td>
                        <input type="text" class="form-control" id="input-${index + 1}-param-1" placeholder="Text" value="${algo.param1}">
                    </td>
                    <td>
                        <input type="text" class="form-control" id="input-${index + 1}-param-2" placeholder="Text" value="${algo.param2}">
                    </td>
                    <td>
                        <input type="text" class="form-control" id="input-${index + 1}-param-3" placeholder="Text" value="${algo.param3}">
                    </td>
                    <td>
                        <span id="status-algo${index + 1}" class="badge bg-secondary">${algo.status}</span>
                    </td>
                    <td>
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" id="flexSwitchCheckDiaoyu-${index + 1}" ${algo.status === 'Active' ? 'checked' : ''} onclick="handleAlgoToggle(this, 'Algo ${index + 1}', 'input-${index + 1}-param-1', 'input-${index + 1}-param-2', 'status-algo${index + 1}')">
                        </div>
                    </td>
                `;
                algoList.appendChild(newRow);
            });
        })
        .catch(error => {
            console.error('Error fetching algo data:', error);
        });
}

// Call the function to fetch data and populate the table when the page loads
document.addEventListener('DOMContentLoaded', fetchAlgoData);

// Handle the toggle change
function handleAlgoToggle(checkbox, algoName, input1, input2, statusId) {
    const statusBadge = document.getElementById(statusId);
    if (checkbox.checked) {
        statusBadge.textContent = `${algoName} Active`;
        statusBadge.classList.remove('bg-secondary');
        statusBadge.classList.add('bg-success');
    } else {
        statusBadge.textContent = `${algoName} Idle`;
        statusBadge.classList.remove('bg-success');
        statusBadge.classList.add('bg-secondary');
    }
}