const leadingExchange = document.getElementById('leading-exchange-input').value;
const laggingExchange = document.getElementById('lagging-exchange-input').value;
const instrument = document.getElementById('instrument-input').value;
let exchange_api_port_map = new Map()
exchange_api_port_map.set('okx','5080')
exchange_api_port_map.set('htx','5081')

// async function handleClick(type) {
//     const token = getAuthToken();
        
//     if (!token) {
//         alert("You must be logged in to access this.");
//         return;
//     }

//     // confirm(`You clicked on ${type} card.`);
//     const instId = document.getElementById('currency-input').value;
//     const sz = document.getElementById('qty-input').value;
//     const username = localStorage.getItem('username')
//     const redis_key = localStorage.getItem('key')
//     const ordType = 'market'
//     const px1 = ''
//     const px2 = ''

//     let side = ''
//     if (type == "buy"){
//         side = 'buy';
//     }    
//     else{
//         side = 'sell'
//     }
//     // console.log(side)
  
//     const orderData = {
//         leadingExchange,
//         laggingExchange,
//         instrument,
//         instId,
//         ordType,
//         px1,
//         px2,
//         sz,
//         side,
//         username,
//         redis_key
//     };
   
//     try {
//         // Set first order price and prepare first order data
//         orderData.px = orderData.px1;
//         const firstOrderPromise = fetch(`http://${hostname}:${exchange_api_port_map.get(leadingExchange)}/${leadingExchange}/${instrument}/place_${ordType}_order`, {
//             method: 'POST',
//             headers: {
//                 'Authorization': `Bearer ${token}`,
//                 'Content-Type': 'application/json',
//             },
//             body: JSON.stringify(orderData)
//         });
    
//         // Prepare second order data
//         const secondOrderData = { ...orderData }; // Clone the order data
//         secondOrderData.side = orderData.side === 'buy' ? 'sell' : 'buy';
//         secondOrderData.px = orderData.px2;
//         console.log('secondOrderData', secondOrderData);
    
//         // Set up second order request
//         const secondOrderPromise = fetch(`http://${hostname}:${exchange_api_port_map.get(laggingExchange)}/${laggingExchange}/${instrument}/place_${ordType}_order`, {
//             method: 'POST',
//             headers: {
//                 'Authorization': `Bearer ${token}`,
//                 'Content-Type': 'application/json',
//             },
//             body: JSON.stringify(secondOrderData)
//         });
    
//         // Run both requests concurrently and wait for both to complete
//         const results = await Promise.allSettled([firstOrderPromise, secondOrderPromise]);
//         if (results[0].status === 'fulfilled' ) {
//             console.log(results)
//             const firstResult = await results[0].value.json();

//             if (firstResult.data[0]['errorCode']| firstResult.data[0]['sCode'] == 400){
//                 console.log("ERROR")
//                 // showToast('Refresh page','info','exchange','ts','orderId',200,'1039')


//                 showToast(`Error with first order: ${firstResult.data[0]['sMsg']}`,`${firstResult.data[0]['exchange']}`,`${firstResult.data[0]['ts']}`, `${firstResult.data[0]['ordId']}`,`${firstResult.data[0]['sCode']}`,`${firstResult.data[0]['errorCode']}`);

//             } 
//             else{
//                 console.log(firstResult)
//                 console.log('Response from first server:', firstResult.data);
//                 showToast(`Success with first order: ${firstResult.data[0]['sMsg']}`,`${firstResult.data[0]['exchange']}`,`${firstResult.data[0]['ts']}`, `${firstResult.data[0]['ordId']}`,`${firstResult.data[0]['sCode']}`,`${firstResult.data[0]['errorCode']}`);

//             }

//         } else {
//             console.error('Error with first order:', results[0].reason);
//             showToast(`Error with first order: ${firstResult.data[0]['sMsg']}`,`${firstResult.data[0]['exchange']}`,`${firstResult.data[0]['ts']}`, `${firstResult.data[0]['ordId']}`,`${firstResult.data[0]['sCode']}`,`${firstResult.data[0]['errorCode']}`);
//         }
    
//         // Handle second order response
//         if (results[1].status === 'fulfilled') {
//             const secondResult = await results[1].value.json();
//             console.log(secondResult)
//             if (secondResult.data[0]['errorCode']| secondResult.data[0]['sCode'] == 400){
//                 console.log("ERROR")
//                 // showToast('Refresh page','info','exchange','ts','orderId',200,'1039')


//                 showToast(`Error with second order: ${secondResult.data[0]['sMsg']}`,`${secondResult.data[0]['exchange']}`,`${secondResult.data[0]['ts']}`, `${secondResult.data[0]['ordId']}`,`${secondResult.data[0]['sCode']}`,`${secondResult.data[0]['errorCode']}`);
                
//             } 
//             else{
//                 console.log(secondResult)
//                 console.log('Response from second server:', secondResult.data);
//                 showToast(`Success with second order: ${secondResult.data[0]['sMsg']}`,`${secondResult.data[0]['exchange']}`,`${secondResult.data[0]['ts']}`, `${secondResult.data[0]['ordId']}`,`${secondResult.data[0]['sCode']}`,`${secondResult.data[0]['errorCode']}`);

//             }
            
           
//         } else {
//             console.error('Error with second order:', results[1].reason);
//             showToast(`Error with second order: ${results[1].reason}`, 4000);
//         }
//         populatePositions()

//     } catch (error) {
//         console.error('Unexpected error while sending order data:', error);
//         showToast('An unexpected error occurred while sending order data.', 4000);
//     }
// }

async function handleClick(type) {
    const token = getAuthToken();

    if (!token) {
        alert("You must be logged in to access this.");
        return;
    }

    const instId = document.getElementById('currency-input').value;
    const sz = document.getElementById('qty-input').value;
    const username = localStorage.getItem('username');
    const redis_key = localStorage.getItem('key');
    const ordType = 'market';
    const px1 = '';
    const px2 = '';

    let side = '';
    if (type == "buy") {
        side = 'buy';
    } else {
        side = 'sell';
    }

    const orderData = {
        leadingExchange,
        laggingExchange,
        instrument,
        instId,
        ordType,
        px1,
        px2,
        sz,
        side,
        username,
        redis_key
    };

    // Set up first order request
    orderData.px = orderData.px1;
    const firstOrderPromise = fetch(`http://${hostname}:${exchange_api_port_map.get(leadingExchange)}/${leadingExchange}/${instrument}/place_${ordType}_order`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData)
    });

    // Prepare second order data
    const secondOrderData = { ...orderData }; // Clone the order data
    secondOrderData.side = orderData.side === 'buy' ? 'sell' : 'buy';
    secondOrderData.px = orderData.px2;
    const secondOrderPromise = fetch(`http://${hostname}:${exchange_api_port_map.get(laggingExchange)}/${laggingExchange}/${instrument}/place_${ordType}_order`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(secondOrderData)
    });

    // Run both requests concurrently without waiting for them to finish
    Promise.allSettled([firstOrderPromise, secondOrderPromise]).then((results) => {
        // Handle first order response
        if (results[0].status === 'fulfilled') {
            results[0].value.json().then(firstResult => {
                if (firstResult.data[0]['errorCode'] || firstResult.data[0]['sCode'] === 400) {
                    showToast(`Error with first order: ${firstResult.data[0]['sMsg']}`, `${firstResult.data[0]['exchange']}`, `${firstResult.data[0]['ts']}`, `${firstResult.data[0]['ordId']}`, `${firstResult.data[0]['sCode']}`, `${firstResult.data[0]['errorCode']}`);
                } else {
                    showToast(`Success with first order: ${firstResult.data[0]['sMsg']}`, `${firstResult.data[0]['exchange']}`, `${firstResult.data[0]['ts']}`, `${firstResult.data[0]['ordId']}`, `${firstResult.data[0]['sCode']}`, `${firstResult.data[0]['errorCode']}`);
                }
            }).catch(error => console.error("Error parsing first order response:", error));
        } else {
            console.error('Error with first order:', results[0].reason);
            showToast(`Error with first order: ${results[0].reason}`, 4000);
        }

        // Handle second order response
        if (results[1].status === 'fulfilled') {
            results[1].value.json().then(secondResult => {
                if (secondResult.data[0]['errorCode'] || secondResult.data[0]['sCode'] === 400) {
                    showToast(`Error with second order: ${secondResult.data[0]['sMsg']}`, `${secondResult.data[0]['exchange']}`, `${secondResult.data[0]['ts']}`, `${secondResult.data[0]['ordId']}`, `${secondResult.data[0]['sCode']}`, `${secondResult.data[0]['errorCode']}`);
                } else {
                    showToast(`Success with second order: ${secondResult.data[0]['sMsg']}`, `${secondResult.data[0]['exchange']}`, `${secondResult.data[0]['ts']}`, `${secondResult.data[0]['ordId']}`, `${secondResult.data[0]['sCode']}`, `${secondResult.data[0]['errorCode']}`);
                }
            }).catch(error => console.error("Error parsing second order response:", error));
        } else {
            console.error('Error with second order:', results[1].reason);
            showToast(`Error with second order: ${results[1].reason}`, 4000);
        }

        // Populate positions asynchronously
        populatePositions();
    }).catch(error => console.error("Error with Promise.allSettled:", error));
}


function showToast(message,  apiSource = 'API',timestamp=null,orderId=null,statusCode=200,errCode =1039) {
    const toastMessage = {
        id: Date.now(),
        message,
        apiSource,
        timestamp,
        orderId,
        statusCode,
        errCode
    };
    notifications.push(toastMessage);
 
    updateNotificationHub();
    updateNotificationCount();
}