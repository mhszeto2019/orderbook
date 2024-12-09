

function handleOrderBookData(exchange, ccy, message,tableNo) {

    const orderDataTableBody = document.getElementById(`order-data-table-body-${tableNo}`);
    orderDataTableBody.innerHTML = ''; // Clears previous data

    // console.log(message)
    // updateBidAndAskPrices(exchange,ccy,message)
    try {
        const { bids, asks, ccy: messageCcy } = typeof message.data === 'string' ? JSON.parse(message.data) : message.data;

        // Check if the currency from the message matches the input 'ccy'
        if (messageCcy !== ccy) {
            // console.log(messageCcy);
            // If no matching data, use last known data
            const lastDataKey = `${exchange}_${ccy}`;
            if (lastData[lastDataKey]) {
                const { bids: lastBids, asks: lastAsks } = lastData[lastDataKey];
                
                const maxLength = Math.max(lastBids.length, lastAsks.length);
                const rows = [];

                // Generate ask rows in reverse order (from lowest to highest)
                for (let i = maxLength - 1; i >= 0; i--) {
                    const ask = lastAsks[i] || ['', ''];
                    rows.push(`<tr><td class="ask-price">${ask[0]}</td><td class="ask-price">${ask[1]}</td></tr>`);
                }

                const livePriceRow = historicalMap[lastDataKey];
                if (livePriceRow) {
                    rows.push(`
                        <tr style="font-weight:bold;">
                            <td>${livePriceRow.lastPrice}</td>
                            <td>${livePriceRow.lastSize}</td>
                        </tr>
                    `);
                }

                // Generate bid rows (from highest to lowest)
                for (let i = 0; i < maxLength; i++) {
                    const bid = lastBids[i] || ['', ''];
                    rows.push(`<tr><td class="bid-price">${bid[0]}</td><td class="bid-price">${bid[1]}</td></tr>`);
                }

                // Update the table with the last known data
                orderDataTableBody.innerHTML = rows.join('');
            } else {
                orderDataTableBody.innerHTML = '<tr><td colspan="2">No data found</td></tr>';
            }
            return;
        }

        // Store the last order book data for this exchange and currency
        lastData[`${exchange}_${ccy}`] = {
            bids: bids,
            asks: asks,
            timestamp: new Date().toISOString() // Store timestamp for last data
        };

        const maxLength = Math.max(bids.length, asks.length);
        const rows = [];

        // Generate ask rows in reverse order (from lowest to highest)
        for (let i = maxLength - 1; i >= 0; i--) {
            const ask = asks[i] || ['', ''];
            rows.push(`<tr><td class="ask-price">${ask[0]}</td><td class="ask-price">${ask[1]}</td></tr>`);
        }

        const livePriceRow = historicalMap[`${exchange}_${ccy}`]  ;

        if (livePriceRow) {
            rows.push(`
                <tr style="font-weight:bold;">
                    <td>${livePriceRow.lastPrice,1}</td>
                    <td>${livePriceRow.lastSize}</td>
                </tr>
            `);
        }

        // Generate bid rows (from highest to lowest)
        for (let i = 0; i < maxLength; i++) {
            const bid = bids[i] || ['', ''];
            rows.push(`<tr><td class="bid-price">${bid[0]}</td><td class="bid-price">${bid[1]}</td></tr>`);
        }

        // Update the table with the generated rows
        orderDataTableBody.innerHTML = rows.join('');
    } catch (error) {
        console.error("Error handling order book data:", error);
    }
}


