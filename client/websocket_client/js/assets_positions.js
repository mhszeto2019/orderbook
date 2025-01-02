const order_management_sockets = {
    asset_positions: io('http://localhost:5021', {
        transports: ['websocket'],
        // debug: false // Disable debug logging
    }),

};

// Optimize connection logging
Object.entries(order_management_sockets).forEach(([name, socket]) => {
    socket.on('connect', () => console.log(`Connected to ${name} WebSocket`));
});

order_management_sockets.asset_positions.onAny((event, message) => handlePriceUpdate(event, message));


function handlePriceUpdate(event,message){
    json_message = JSON.parse(message)

    console.log(json_message)
    
    // Assuming message contains the required data, modify according to your data structure
    const data = json_message.data[0];
    const currency = data.balData[0].ccy;
    const cashBal = data.balData[0].cashBal;
    const instId = data.posData[0].instId;
    const position = data.posData[0].pos;
    const avgPx = data.posData[0].avgPx;
    const posSide = data.posData[0].posSide;

    // Create a table row with the new data
    const assetsPositionsRow = `
        <tr>
            <td>${currency}</td>
            <td>${cashBal}</td>
            <td>${instId}</td>
            <td>${position}</td>
            <td>${avgPx}</td>
            <td>${posSide}</td>
        </tr>
    `;

    // Update the content of the "open-orders-body" (this will not affect the table headers)
    document.getElementById('oms-assets-positions-body').innerHTML = assetsPositionsRow;
}