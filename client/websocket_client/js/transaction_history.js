    // Function to refresh data when the button is clicked
    
    async function refreshTransactionHistory() {
        console.log("Refreshing transaction history...");
        const hostname = window.location.hostname
        try {
            // Fetch data from the API
            const response = await fetch(`http://${hostname}:5022/get_fills`);
            if (!response.ok) {
                throw new Error("Network response was not ok " + response.statusText);
            }

            // Parse the JSON data from the API response
            const response_json = await response.json();
            data = response_json.data
            channel = 'txn-history'
            console.log(data)
            // Assuming `data` is an array of transaction objects
            let tableRows = "";
            data.forEach((txn) => {
                console.log(txn.ts)
                tableRows += `
                    <tr>
                        <td>${txn.instId}</td>
                        <td>${txn.fillPx}</td>
                        <td>${txn.fillSz}</td>
                        <td>${txn.fillTime}</td>
                        <td>${txn.instType}</td>
                        <td>${txn.fee}</td>
                        <td>${txn.feeCcy}</td>
                        <td>${new Date(txn.ts/1000).toLocaleString()}</td>
                    </tr>
                `;
            });

            // Update the table with the new data
            document.getElementById(`oms-open-${channel}-body`).innerHTML = tableRows;

            // Update the last updated time
            document.getElementById(`last-updated-${channel}`).innerText = new Date().toLocaleString();

        } catch (error) {
            console.error("Error fetching transaction history:", error);
        }
    }

        

    