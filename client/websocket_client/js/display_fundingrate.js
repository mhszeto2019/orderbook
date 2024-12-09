
async function populateFundingRate
(){
    const token = getAuthToken();
    const username = localStorage.getItem('username');
    const redis_key = localStorage.getItem('key');


    if (!token || !username || !redis_key) {
        alert("You must be logged in to access this.");
        return;
    }
    ccy = document.getElementById('currency-input').value

    const request_data = { "username": username, "redis_key": redis_key,'ccy':ccy };

    const firstOrderPromise = fetch(`http://${hostname}:5001/okx/getfundingrate`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request_data)
    });
    const secondOrderPromise = fetch(`http://${hostname}:5002/htx/getfundingrate`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request_data)
    });
    const results = await Promise.allSettled([firstOrderPromise,secondOrderPromise]);

    // Array to hold combined funding rate
    let allFundingRate = [];

    // Handle OKX Response
    if (results[0].status === 'fulfilled') {
        const response = results[0].value;
        if (response.ok) {
            const response_data = await response.json();
            data = response_data.data[0]
            // const FundingTime = data.fundingTime;
            // console.log(data.fundingTime)
            const humanReadableFundingTime  = unixTsConversion(data.fundingTime)
            const humanReadableNextFundingTime  = unixTsConversion(data.nextFundingTime)
            const currencyValue = parseFloat(data.fundingRate); // Parse the value to ensure it's a number
                if (!isNaN(currencyValue)) {
                    fundingRate = `${(currencyValue * 100).toFixed(6)}%`; // Convert to percentage
                } else {
                    fundingRate = "Invalid value"; // Handle invalid input
                }
            if (response_data.data){
                // Append OKX data to allOpenOrders
                document.getElementById('funding-time-okx').textContent = `${humanReadableFundingTime}`;
                document.getElementById('next-funding-time-okx').textContent = `${humanReadableNextFundingTime}`;
                document.getElementById('funding-rate-okx').textContent = `${fundingRate}`;
                document.getElementById('currency-okx').textContent = `${data.currency}`;
                
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

    if (results[1].status === 'fulfilled') {
        const response = results[1].value;
        if (response.ok) {
            const response_data = await response.json();
            console.log(response_data)
            data = response_data
            console.log(data)
            
            const humanReadableFundingTime  = unixTsConversion(data.funding_time)
            const humanReadableNextFundingTime  = unixTsConversion(data.next_funding_time)
            const currencyValue = parseFloat(data.funding_rate); // Parse the value to ensure it's a number
                if (!isNaN(currencyValue)) {
                    fundingRate = `${(currencyValue * 100).toFixed(6)}%`; // Convert to percentage
                } else {
                    fundingRate = "Invalid value"; // Handle invalid input
                }
            if (response_data){
                // Append OKX data to allOpenOrders
                document.getElementById('funding-time-htx').textContent = `${humanReadableFundingTime}`;
                document.getElementById('next-funding-time-htx').textContent = `${humanReadableNextFundingTime}`;
                document.getElementById('funding-rate-htx').textContent = `${fundingRate}`;
                document.getElementById('currency-htx').textContent = `${data.contract_code}`;
                
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
}


function unixTsConversion(timestampString){
    timestamp = Number(timestampString);
    if (!timestamp || isNaN(timestamp)) {
        return "Invalid timestamp";
    }
    
    // Convert the timestamp to a Date object
    const date = new Date(timestamp);
    console.log(date)
    // Format the date to a human-readable string
    return date.toLocaleString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        timeZoneName: "short" // Includes the time zone
    });
}

// // // Set up the scheduler
function startFundingRateScheduler(interval = 35000) {
    // Call populateFundingRate immediately
    populateFundingRate();

    // Schedule populateFundingRate to run every few seconds
    setInterval(populateFundingRate, interval);
}

// Start the scheduler when the page loads
document.addEventListener('DOMContentLoaded', () => {
    startFundingRateScheduler();
});
