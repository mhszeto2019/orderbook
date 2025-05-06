// const leadingExchange = document.getElementById('exchange1-input').value;
// const laggingExchange = document.getElementById('exchange2-input').value;

// const marketType1 = document.getElementById('market-type-orderbook1').value;
// const marketType2 = document.getElementById('market-type-orderbook2').value;

// const instrument1 = document.getElementById('currency-input-orderbook1').value;
// const instrument2 = document.getElementById('currency-input-orderbook2').value;


let exchange_api_port_map = new Map()
exchange_api_port_map.set('okxperp','5080')
exchange_api_port_map.set('htxperp','5081')
exchange_api_port_map.set('deribitperp','5082')
exchange_api_port_map.set('binanceperp','5083')
exchange_api_port_map.set('binancespot','5084')



function showDone(message, error = false) {
    const container = document.getElementById('toast-container');

    const toastEl = document.createElement('div');
    toastEl.className = 'toast fade';
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');

    toastEl.innerHTML = `
        <div class="toast-header buy-sell-toast-container">
            <strong class="me-auto">${error ? 'Error' : 'Notice'}</strong>
            <small>just now</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body buy-sell-toast-container ${error ? 'text-error' : ''}">
            ${message}
        </div>
    `;

    container.appendChild(toastEl);

    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: 3000
    });

    toast.show();

    // Optional: remove toast from DOM after it's hidden
    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}

async function handleClick(type) {
    const token = getAuthToken();
    if (!token) {
        alert("You must be logged in to access this.");
        return;
    }

    const leadingExchange = document.getElementById('exchange1-input').value;
    const laggingExchange = document.getElementById('exchange2-input').value;

    const marketType1 = document.getElementById('market-type-orderbook1').value;
    const marketType2 = document.getElementById('market-type-orderbook2').value;

    const instrument1 = document.getElementById('currency-input-orderbook1').value;
    const instrument2 = document.getElementById('currency-input-orderbook2').value;
    
    const offset1 = document.getElementById('htx-open-close-1').value;
    const offset2 = document.getElementById('htx-open-close-2').value;

    // const instId = document.getElementById('currency-input').value;
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
    if (leadingExchange == 'htx'){
        validateSelectInput('htx-open-close-1')
        if (!offset2){
      
          
            return
        }
    }
    if (laggingExchange == 'htx'){
        console.log("lag")
        validateSelectInput('htx-open-close-2')


        if (!offset2){
         
            return
        }
    }

    const orderData = {
        leadingExchange,
        laggingExchange,
        instrument1,
        instrument2,
        ordType,
        px1,
        px2,
        sz,
        side,
        username,
        redis_key,
        offset1,
        offset2
    };

    fastapi_folder1 = leadingExchange + marketType1
    fastapi_folder2 = laggingExchange + marketType2

    // console.log(fastapi_folder1,fastapi_folder2)
    // console.log(offset1,offset2)
    // Set up first order request
    orderData.px = orderData.px1;
    orderData.instrument = orderData.instrument1;
    orderData.offset = orderData.offset1;

    const firstOrderPromise = fetch(`http://${hostname}:${exchange_api_port_map.get(fastapi_folder1)}/${fastapi_folder1}/place_order`, {
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
    secondOrderData.instrument = orderData.instrument2;
    secondOrderData.offset = orderData.offset2;


    const secondOrderPromise = fetch(`http://${hostname}:${exchange_api_port_map.get(fastapi_folder2)}/${fastapi_folder2}/place_order`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(secondOrderData)
    });
    const results = await Promise.allSettled([firstOrderPromise, secondOrderPromise])
    console.log("RESULTSSSSSSSSSSSSSSSSSSSSSSS",results)
    if (results[0].status === 'fulfilled') {
                
        const firstResult = await results[0].value.json();

        if (firstResult['error']) {
            showToast(firstResult['error'])
            showDone(`${firstResult['error']}`,true)

        } else {
            console.log("DONEE SUCCESSSSS")
            firstResult.info['exchange'] = fastapi_folder2
            showToast(JSON.stringify(firstResult.info))
            showDone(`${fastapi_folder1}-PLACE ORDER SUCCESS`,false)

        }
    }

    if (results[1].status === 'fulfilled') {
               
                
        const secondResult = await results[1].value.json();

        if (secondResult['error']) {
            showToast(secondResult['error'])
            showDone(`${secondResult['error']}`,true)

        } else {
            console.log("DONEE SUCCESSSSS")
            secondResult.info['exchange'] = fastapi_folder2
            showToast(JSON.stringify(secondResult.info))
            showDone(`${fastapi_folder2}-PLACE ORDER SUCCESS`,false)

        }
    }


    // Run both requests concurrently without waiting for them to finish
    // Promise.allSettled([firstOrderPromise, secondOrderPromise]).then((results) => {
    //     // Handle first order response
    //     console.log(results[0])
    //     if (results.status === 'fulfilled') {
    //         results.value.json().then(firstResult => {
    //             if (firstResult.data[0]['errorCode'] || firstResult.data[0]['sCode'] === 400) {
    //                 showToast(`Error with first order: ${firstResult.data[0]['sMsg']}`, `${firstResult.data[0]['exchange']}`, `${firstResult.data[0]['ts']}`, `${firstResult.data[0]['ordId']}`, `${firstResult.data[0]['sCode']}`, `${firstResult.data[0]['errorCode']}`);
    //             } else {
    //                 // showToast(`Success with first order: ${firstResult.data[0]['sMsg']}`, `${firstResult.data[0]['exchange']}`, `${firstResult.data[0]['ts']}`, `${firstResult.data[0]['ordId']}`, `${firstResult.data[0]['sCode']}`, `${firstResult.data[0]['errorCode']}`);
    //                 // showDone('hello',true)
    //                 showToast(JSON.stringify(firstResult.info))
    //                 showDone(`${fastapi_folder1}-PLACE ORDER SUCCESS`,false)
    //             }
    //         }).catch(error => console.error("Error parsing first order response:", error));
    //     } else {
    //         console.error('Error with first order:', results[0].reason);
    //         showToast(`Error with first order: ${results[0].reason}`, 4000);
    //     }

    //     // Handle second order response
    //     // if (results.status === 'fulfilled') {
    //     //     results.value.json().then(secondResult => {
    //     //         if (secondResult.data[0]['errorCode'] || secondResult.data[0]['sCode'] === 400) {
    //     //             showToast(`Error with second order: ${secondResult.data[0]['sMsg']}`, `${secondResult.data[0]['exchange']}`, `${secondResult.data[0]['ts']}`, `${secondResult.data[0]['ordId']}`, `${secondResult.data[0]['sCode']}`, `${secondResult.data[0]['errorCode']}`);
    //     //         } else {
    //     //             showToast(`Success with second order: ${secondResult.data[0]['sMsg']}`, `${secondResult.data[0]['exchange']}`, `${secondResult.data[0]['ts']}`, `${secondResult.data[0]['ordId']}`, `${secondResult.data[0]['sCode']}`, `${secondResult.data[0]['errorCode']}`);
    //     //         }
    //     //     }).catch(error => console.error("Error parsing second order response:", error));
    //     // } else {
    //     //     console.error('Error with second order:', results[1].reason);
    //     //     showToast(`Error with second order: ${results[1].reason}`, 4000);
    //     // }

    //     // Populate positions asynchronously
    //     populatePositions();
    // }).catch(error => console.error("Error with Promise.allSettled:", error));
}


function repopulateArbBtnData(){
    document.getElementById("arbButton-bid-buy").textContent = document.getElementById("exchange1-input").value
    document.getElementById("arbButton-bid-sell").textContent = document.getElementById("exchange2-input").value
    
    
    document.getElementById("arbButton-ask-buy").textContent = document.getElementById("exchange2-input").value
    document.getElementById("arbButton-ask-sell").textContent = document.getElementById("exchange1-input").value
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

function validateSelectInput(selectId) {
    const select = document.getElementById(selectId);
    if (select.value === "") {
        select.classList.add("invalid-select");
     
        // Swal.fire({
        //     title: "Missing Item!",
        //     text: "Select Open/Close",
        //     icon: "warning"
        //   });

        Swal.fire({
            title: "Missing Item!",
            text: "Select Open/Close",
            icon: "warning",
            background: '#333', // Dark background color
            color: '#fff', // White text color
            confirmButtonColor: '#1e90ff', // Blue confirm button color
        });

        return false;
    } else {
        select.classList.remove("invalid-select");
        return true;
    }
}
