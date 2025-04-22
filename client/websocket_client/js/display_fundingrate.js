
async function populateFundingRate(){
    const token = getAuthToken();
    const username = localStorage.getItem('username');
    const redis_key = localStorage.getItem('key');

    funding_rates_list = [
        { exchange: 'okxperp', port: 5001 },
        { exchange: 'htxperp', port: 5002 },

    ]


    if (!token || !username || !redis_key) {
        // alert("You must be logged in to access this.");
        return;
    }
    // console.log(document.getElementById('fundingrate-currency-input'))
    ccy = document.getElementById('fundingrate-currency-input').value
    const request_data = { "username": username, "redis_key": redis_key,'ccy':ccy };

    const fetchPromises = funding_rates_list.map(row => {
        return fetch(`http://${hostname}:${row.port}/${row.exchange}/funding_rate`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(request_data)
        });
      });
        
    async function processResults() {
    try {
        const results = await Promise.allSettled(fetchPromises);  // Wait for all fetches to complete
        // Loop through each result and handle it
        for (const [index, result] of results.entries()) {
        if (result.status === 'fulfilled') {
            const response = result.value;
            if (response.ok) {
            const response_data = await response.json();
            exchange = response_data.exchange
            // console.log(response_data)
            // Convert Unix timestamp
            const ts = unixTsConversion(response_data.ts);
            
            // Parse and process the funding rate
            let fundingRate = "Invalid value"; // Default value
            const currencyValue = parseFloat(response_data.funding_rate);
            if (!isNaN(currencyValue)) {
                fundingRate = `${(currencyValue * 100).toFixed(6)}%`; // Convert to percentage
            }

            // Handle the response data
            if (response_data) {
                // Example of setting the data in HTML elements
                document.getElementById(`fundingratets-${exchange}`).textContent = `${ts}`;
                document.getElementById(`funding-rate-${exchange}`).textContent = `${fundingRate}`;
                document.getElementById(`currency-${exchange}`).textContent = `${response_data.ccy }`;
            }
            } else {
            console.error(`Error fetching funding rate from exchange ${exchange}:`, response.statusText);
            }
        } else {
            console.error(`Request failed for exchange ${index + 1}:`, result.reason);
        }
        }
    } catch (error) {
        console.error("Error during fetch execution:", error);
    }
    }

    // Call the processResults function
    processResults();
}

function unixTsConversion(timestampString) {
    const timestamp = Number(timestampString);
    if (!timestamp || isNaN(timestamp)) {
        return "Invalid timestamp";
    }

    // Convert the timestamp to a Date object
    const date = new Date(timestamp);

    // Extract the components of the date
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0"); // Month is 0-indexed
    const year = String(date.getFullYear()).slice(-2); // Get last 2 digits of year
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    const seconds = String(date.getSeconds()).padStart(2, "0");
    const milliseconds = String(date.getMilliseconds()).padStart(3, "0");

    // Format as dd/mm/yy hh:mm:ss:ms
    return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}:${milliseconds}`;
}

// Example usage:
// console.log(unixTsConversion("1700000000000"));  // Example timestamp


// // // Set up the scheduler
function startFundingRateScheduler(interval = 5000) {
    // Call populateFundingRate immediately
    populateFundingRate();
    

    // Schedule populateFundingRate to run every few seconds
    setInterval(populateFundingRate, interval);
}

// Start the scheduler when the page loads
document.addEventListener('DOMContentLoaded', () => {
    startFundingRateScheduler();
});
