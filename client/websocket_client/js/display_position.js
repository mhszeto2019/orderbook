// oms-open-positions-body

async function populatePositions() {
    const openPositionDOM = document.getElementById('oms-open-positions-body');
    openPositionDOM.innerHTML = '';  // Clear the table before populating
    const openPositionTS = document.getElementById('last-updated-positions');
    let onePositionTs =''
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
    const firstOrderPromise = fetch(`http://${hostname}:5070/okxperp/get_all_positions`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request_data)
    });

    const secondOrderPromise = fetch(`http://${hostname}:5071/htxperp/get_all_positions`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request_data)
    });

    const thirdOrderPromise = fetch(`http://${hostname}:5072/deribitperp/get_all_positions`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request_data)
    });


    const fourthOrderPromise = fetch(`http://${hostname}:5073/binanceperp/get_all_positions`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request_data)
    });


    try {
        document.getElementById('oms-open-positions-body').innerHTML = `
           <tr>
            <td colspan="9" class="text-center text-muted">
            <div class="d-flex justify-content-center align-items-center gap-2">
                <div class="spinner-border spinner-border-sm text-secondary" role="status" aria-hidden="true"></div>
                <span>Loading...</span>
            </div>
            </td>
        </tr>
        `;
        const Promises = await Promise.allSettled([firstOrderPromise, secondOrderPromise,thirdOrderPromise,fourthOrderPromise]);

        // Array to hold combined positions
        let allPositions = [];


        // Handle OKX Response
        if (Promises[0] && Promises[0].status === 'fulfilled') {
            const pos = Promises[0].value;

            if (pos.ok) {
                let posData = await pos.json()
                if (posData){
                    console.log(posData)
                        posData.forEach(posRow => {
                            // console.log(posRow)
                            allPositions.push(posRow)
                        }
                    )
                }
            }

            else {
                console.error('OKX Request failed:',  Promises[0].status);
        } 
        }
        if (Promises[1] && Promises[1].status === 'fulfilled') {
            const pos = Promises[1].value;
            // console.log(pos)

            if (pos.ok) {
                let posData = await pos.json()
                if (posData){
                    console.log(posData)
                        posData.forEach(posRow => {
                            // console.log(posRow)
                            allPositions.push(posRow)
                        }
                    )
                }
            }
            
            else {
                console.error('HTX Request failed:', Promises[1].status);
            }
        } 

        if (Promises[2] && Promises[2].status === 'fulfilled') {
            const pos = Promises[2].value;
            // console.log(pos)

            if (pos.ok) {
                let posData = await pos.json()
                if (posData){
                    console.log(posData)
                        posData.forEach(posRow => {
                            // console.log(posRow)
                            allPositions.push(posRow)
                        }
                    )
                }
            }
            else {
                console.error('DERIBIT Request failed:', Promises[2].status);
            }
            
        } 

        if (Promises[3] && Promises[3].status === 'fulfilled') {
            const pos = Promises[3].value;
            // console.log(pos)

            if (pos.ok) {
                let posData = await pos.json()
                if (posData){
                    console.log(posData)
                        posData.forEach(posRow => {
                            // console.log(posRow)
                            allPositions.push(posRow)
                        }
                    )
                }
            }
            else {
                console.error('BINANCE Request failed:', Promises[3].status);
            }
            
        } 

       
        // After both positioinResponses are handled, populate the table with all positions
        populateOpenPositionsTable(allPositions);

    } catch (error) {
        console.error('Error in fetching and populating data:', error);
    }
}




function populateOpenPositionsTable(positions) {
    const omsTable = $('.OMStable').DataTable();
    omsTable.clear();
    
    if (positions.length === 0) {
        omsTable.clear().draw();
        $('#oms-open-positions-body').html(
            '<tr><td colspan="9" class="dataTables_empty">No open positions available</td></tr>'
        );
    } else {
        positions.forEach(position => {
            omsTable.row.add([
                position.exchange || 'N/A',
                position.instrument_id || 'N/A',
                position.leverage || 'N/A',
                position.position ? Number(position.position).toFixed(2) : 'N/A',
                position.adl || 'N/A',
                position.liquidation_price ? Number(position.liquidation_price).toFixed(2) : 'N/A',
                position.price ? Number(position.price).toFixed(2) : 'N/A',
                position.pnl ? Number(position.pnl).toFixed(10) : 'N/A',
                position.ts ? new Date(parseInt(position.ts)).toLocaleString() : 'N/A'
            ]);
        });
        omsTable.draw(false);
    }
    omsTable.columns.adjust().draw(false);
}



// function Htx2OkxFormat(originalDataArray) {
//     console.log('ori',originalDataArray)
//     return originalDataArray.map(originalData => {
//       return {
//         "adl": String(originalData.open_adl || '0'),  // Convert to string, or default to 0
//         "availPos": "",  // Empty as per the target format
//         "avgPx": String(originalData.last_price.toFixed(1)),  // Rounded to 1 decimal place
//         "baseBal": "",
//         "baseBorrowed": "",
//         "baseInterest": "",
//         "bePx": originalData.liq_px === null ? null : String(originalData.liq_px.toFixed(10)),  // Displaying the value with 10 decimal points
//         "bizRefId": "",
//         "bizRefType": "",
//         "cTime": new Date(originalData.store_time).getTime().toString(),  // Convert to timestamp
//         "ccy": originalData.symbol,
//         "clSpotInUseAmt": "",
//         "closeOrderAlgo": [],
//         "deltaBS": "",
//         "deltaPA": "",
//         "fee": String(originalData.profit_rate.toFixed(10)),  // Rounding for consistency
//         "fundingFee": "0",
//         "gammaBS": "",
//         "gammaPA": "",
//         "idxPx": String(originalData.cost_open.toFixed(10)),  // Using cost_open for idxPx
//         "imr": "",
//         "instId": originalData.contract_code + "-SWAP",  // Assuming this is a swap contract
//         "instType": "SWAP",
//         "interest": "",
//         "last": String(originalData.last_price.toFixed(1)),
//         "lever": String(originalData.lever_rate),
//         "liab": "",
//         "liabCcy": "",
//         "liqPenalty": "0",
//         "liqPx": originalData.liq_px === null ? null : String(originalData.liq_px.toFixed(10)),
//         "margin": String(originalData.position_margin.toFixed(10)),
//         "markPx": String(originalData.last_price.toFixed(1)),
//         "maxSpotInUseAmt": "",
//         "mgnMode": "isolated",
//         "mgnRatio": "",  // Assumed fixed value for this example
//         "mmr": String((originalData.profit / originalData.cost_hold).toFixed(10)),  // Just an example calculation
//         "notionalUsd": "",  // Assumed fixed value
//         "optVal": "",
//         "pendingCloseOrdLiabVal": "",
//         "pnl": String(originalData.profit.toFixed(10)),  // Placeholder, may depend on further logic
//         "pos": originalData.direction === "sell" ? String(-Math.abs(originalData.volume)): String(originalData.volume),  // Placeholder for position status
//         "posCcy": "",
//         "posId": "2019681002234920961",  // Placeholder position ID
//         "posSide": String((originalData.direction)),  // Assumed position side
//         "quoteBal": "",
//         "quoteBorrowed": "",
//         "quoteInterest": "",
//         "realizedPnl": String(originalData.profit.toFixed(10)),
//         "spotInUseAmt": "",
//         "spotInUseCcy": "",
//         "thetaBS": "",
//         "thetaPA": "",
//         "tradeId": "333006380",  // Placeholder trade ID
//         "uTime": new Date(originalData.store_time).getTime().toString(),
//         "upl": String(originalData.profit.toFixed(10)),
//         "uplLastPx": String(originalData.profit.toFixed(10)),
//         "uplRatio": String((originalData.profit_rate).toFixed(10)),
//         "uplRatioLastPx": String((originalData.profit_rate).toFixed(10)),
//         "usdPx": "",
//         "vegaBS": "",
//         "vegaPA": "",
//         "exchange":'htx'
//       };
//     });
//   }


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