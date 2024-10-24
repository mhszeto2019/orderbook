
const hostname = window.location.hostname;
// const hostname = "192.168.0.235"
console.log("HELLLLLLLLLLLL")
console.log(hostname)


const order_management_sockets = {
    oms: io(`http://${hostname}:5021`, {
        transports: ['websocket'],
        debug: true // Disable debug logging
    }),

};



// Optimize connection logging
Object.entries(order_management_sockets).forEach(([name, socket]) => {
    socket.on('connect', () => console.log(`Connected to ${name} WebSocket`));
});

order_management_sockets.oms.onAny((websocket_connection_name, message) => handlePriceUpdate(websocket_connection_name, message));



function handlePriceUpdate(websocket_connection_name,message){
    // console.log(websocket_connection_name)
    // console.log(typeof message)
    // console.log(message)
    // console.log(message.event)
    if (!message.event){
        const channel = message.channel
        const data = message.data ? message.data:null
        const time_of_snaphsot = data[0] ? data[0].pTime: 0
       
        if (channel== "orders"){
         // Loop through the 'closeOrderAlgo' array
               // Assuming data is an array of objects
               let table = ``
             
               // Loop through the list of dictionaries (dataList)
               data.forEach((data) => {
                   // Calculate liqPrice - markPx for each row
                   const liqPriceDifference = (parseFloat(data.liqPx) - parseFloat(data.markPx)).toFixed(6);

                   // Generate a table row in the required order
                   let row = `<tr>
                       <td>${data.cTime}</td>
                       <td>${data.fillTime}</td>
                       <td>${data.side}</td>
                       <td>'limit_Exchange'</td>
                       <td>'Market Exchhange'</td>
                       <td>'Spread'</td>
                       <td>${data.sz}</td>
                       <td>${data.fillSz}</td>
                       <td>'Avg fill spread'</td>
                       <td>
                        <button>Modify</button>
                        <button>Cancel</button>
                       </td>
                       

                   </tr>`;

                   // Assuming you want to append the row to an HTML table with id 'myTable'
                   // document.querySelector('#myTable tbody').innerHTML += row;
                   table += row
               });


               document.getElementById(`oms-open-${channel}-body`).innerHTML = table
        }

        else if (channel =="balance_and_position")
        {
            console.log(channel)
            console.log(time_of_snaphsot)
            console.log('balance',balData)
            
            console.log('position',posData)

            console.log('trades',trades)
            
            
        }
        else if (channel =="positions")
            {
                console.log(channel)
                console.log(time_of_snaphsot)

                // Loop through the 'closeOrderAlgo' array
               // Assuming data is an array of objects
                let table = ``
             
                // Loop through the list of dictionaries (dataList)
                data.forEach((data) => {
                    // Calculate liqPrice - markPx for each row
                    const liqPriceDifference = (parseFloat(data.liqPx) - parseFloat(data.markPx)).toFixed(6);

                    // Generate a table row in the required order
                    let row = `<tr>
                        <td>${data.instId}</td>
                        <td>${data.lever}</td>
                        <td>${data.posSide}</td>
                        <td>${data.availPos}</td>
                        <td>${data.adl}</td>
                        <td>${data.liqPx}</td>
                        <td>${liqPriceDifference}</td>
                        <td>${data.pnl}</td>
                    </tr>`;

                    // Assuming you want to append the row to an HTML table with id 'myTable'
                    // document.querySelector('#myTable tbody').innerHTML += row;
                    table += row
                });


                document.getElementById(`oms-open-${channel}-body`).innerHTML = table
                
            }


    }
  
}