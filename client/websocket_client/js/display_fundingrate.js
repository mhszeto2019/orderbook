
async function populateFundingRate
(){
    const token = getAuthToken();
    const username = localStorage.getItem('username');
    const redis_key = localStorage.getItem('key');


    if (!token || !username || !redis_key) {
        alert("You must be logged in to access this.");
        return;
    }

    const request_data = { "username": username, "redis_key": redis_key };

    const firstOrderPromise = fetch(`http://${hostname}:5001/okx/getfundingrate`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request_data)
    });
    const results = await Promise.allSettled([firstOrderPromise]);

    // Array to hold combined orders
    let allOpenOrders = [];

    // Handle OKX Response
    if (results[0].status === 'fulfilled') {
        const response = results[0].value;
        if (response.ok) {
            const response_data = await response.json();
            data = response_data.data[0]
            // const FundingTime = data.fundingTime;
            const humanReadableFundingTime  = unixTsConversion(data.fundingTime)
            const humanReadableNextFundingTime  = unixTsConversion(data.nextFundingTime)
            
            if (response_data.data){
                // Append OKX data to allOpenOrders
                // console.log(data)
                // console.log(data.fundingRate)
                // console.log(data.fundingTime)
                // console.log(data.instId)
                // console.log(data.instType)
                // console.log(data.nextFundingTime)
                document.getElementById('funding-time-okx').textContent = `Funding Time: ${humanReadableFundingTime}`;
                document.getElementById('next-funding-time-okx').textContent = `Next Funding Time: ${humanReadableNextFundingTime}`;
                document.getElementById('funding-rate-okx').textContent = `Funding Rate: ${data.fundingRate}`;
                document.getElementById('currency-okx').textContent = `Currency: ${data.currency}`;


                
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
}

function unixTsConversion(unixTs){
    return new Date(unixTs * 1000).toLocaleString(); // Convert timestamp to readable format
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
