// oms-open-positions-body

async function populatePositions() {
    const openPositionDOM = document.getElementById('oms-open-positions-body');
    openPositionDOM.innerHTML = '';  // Clear the table before populating
    const openPositionTS = document.getElementById('last-updated-positions');
    onePositionTs =''
    updateTime(openPositionTS);  // Update the timestamp of when the data was last fetched

    const token = getAuthToken();
    const username = localStorage.getItem('username');
    const redis_key = localStorage.getItem('key');

    if (!token || !username || !redis_key) {
        // alert("You must be logged in to access this.");
        return;
    }

    const request_data = { "username": username, "redis_key": redis_key };

    // Set up both the OKX and HTX requests
    const firstOrderPromise = fetch(`http://${hostname}:5070/okx/get_all_positions`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request_data)
    });

    const secondOrderPromise = fetch(`http://${hostname}:5071/htx/get_all_positions`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request_data)
    });

    try {
        const positioinResults = await Promise.allSettled([firstOrderPromise, secondOrderPromise]);

        // Array to hold combined positions
        let allPositions = [];

        // Handle OKX Response
        if (positioinResults[0].status === 'fulfilled') {
            const positioinResponse = positioinResults[0].value;
            if (positioinResponse.ok) {
                const positioinResponse_data = await positioinResponse.json();

                if (positioinResponse_data.data){
                    // Append OKX data to allPositions
                    allPositions = allPositions.concat(positioinResponse_data.data.map(position => ({
                        ...position,
                        exchange: 'OKX'  // Add exchange name to each position
                    })));
                }
                else{
                    console.error(positioinResponse_data['msg'],positioinResponse_data['code'])
                }
                
            } else {
                console.error('Error fetching OKX positions:', positioinResponse.statusText);
            }
        } else {
            console.error('OKX Request failed:', positioinResults[0].reason);
        }

        // Handle HTX Response
        if (positioinResults[1].status === 'fulfilled') {
            const positioinResponse = positioinResults[1].value;
            
            if (positioinResponse.ok) {
                const positioinResponse_data = await positioinResponse.json();
                const formattedData = Htx2OkxFormat(positioinResponse_data);  // Format HTX data as needed
                // Append HTX data to allPositions
                allPositions = allPositions.concat(formattedData.map(position => ({
                    ...position,
                    exchange: 'HTX'  // Add exchange name to each position
                })));
            } else {
                console.error('Error fetching HTX positions:', positioinResponse.statusText);
            }
        } else {
            console.error('HTX Request failed:', positioinResults[1].reason);
        }

        // After both positioinResponses are handled, populate the table with all positions
        populateOpenPositionsTable(allPositions);

    } catch (error) {
        console.error('Error in fetching and populating data:', error);
    }
}




function populateOpenPositionsTable(positions) {
    // Get reference to the DataTable instance (or initialize if not already)
    const omsTable = $('.OMStable').DataTable();
    // Clear existing rows from DataTable
    omsTable.clear();

    if (positions.length === 0) {
        // Add a "No open positions available" message
        // omsTable.row.add([
        //     { display: "No open positions available", colspan: 10 }
            
        // ]);
        // omsTable.row.add([
        //     'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'
        // ]);
           // Clear table
        omsTable.clear();

        // Manually add a row with `colspan`
        const emptyMessage = `
            <tr>
                <td colspan="10" class="text-center text-muted">No open positions available</td>
            </tr>`;
        $('#oms-open-positions-body').html(emptyMessage);
    } else {
        // Add rows dynamically
        positions.forEach(position => {
            omsTable.row.add([
                position.exchange || 'N/A',  // New exchange column
                position.instId || 'N/A',
                position.lever || 'N/A',
                position.mgnRatio ? Number.parseFloat(position.mgnRatio).toFixed(2) : 'N/A',
                position.pos || 'N/A',
                position.adl || 'N/A',
                position.liqPx ? Number.parseFloat(position.liqPx).toFixed(2) : 'N/A',
                position.avgPx || 'N/A',
                position.pnl ? Number.parseFloat(position.pnl).toFixed(10) : 'N/A',
                position.cTime ? new Date(parseInt(position.cTime)).toLocaleString() : 'N/A'
            ]);
        });
    }

    // Redraw the table to reflect changes
    omsTable.draw();
}



function Htx2OkxFormat(originalDataArray) {
    console.log('ori',originalDataArray)
    return originalDataArray.map(originalData => {
      return {
        "adl": String(originalData.open_adl || '0'),  // Convert to string, or default to 0
        "availPos": "",  // Empty as per the target format
        "avgPx": String(originalData.last_price.toFixed(1)),  // Rounded to 1 decimal place
        "baseBal": "",
        "baseBorrowed": "",
        "baseInterest": "",
        "bePx": originalData.liq_px === null ? null : String(originalData.liq_px.toFixed(10)),  // Displaying the value with 10 decimal points
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
        "liqPx": originalData.liq_px === null ? null : String(originalData.liq_px.toFixed(10)),
        "margin": String(originalData.position_margin.toFixed(10)),
        "markPx": String(originalData.last_price.toFixed(1)),
        "maxSpotInUseAmt": "",
        "mgnMode": "isolated",
        "mgnRatio": "",  // Assumed fixed value for this example
        "mmr": String((originalData.profit / originalData.cost_hold).toFixed(10)),  // Just an example calculation
        "notionalUsd": "",  // Assumed fixed value
        "optVal": "",
        "pendingCloseOrdLiabVal": "",
        "pnl": String(originalData.profit.toFixed(10)),  // Placeholder, may depend on further logic
        "pos": originalData.direction === "sell" ? String(-Math.abs(originalData.volume)): String(originalData.volume),  // Placeholder for position status
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
// function startPositionScheduler(interval = 5000) {
//     // Call populatePositions immediately
//     populatePositions();

//     // Schedule populatePositions to run every few seconds
//     setInterval(populatePositions, interval);
// }

// // Start the scheduler when the page loads
// document.addEventListener('DOMContentLoaded', () => {
//     startPositionScheduler();
// });