const hostname = window.location.hostname;

document.addEventListener('DOMContentLoaded', () => {
    function getAuthToken() {
        return localStorage.getItem('jwt_token'); // You may use sessionStorage instead if preferred
    }

    function showToast(message,apiSource = 'API',timestamp=null,orderId=null,statusCode=200,errCode =1039) {
       
        console.log(message,'intoast')
        notifications.push(message);
        console.log(notifications)

        updateNotificationHub();
        updateNotificationCount();
    }

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
    
    // showToast('Refresh page','exchange','ts',null,400,'undefined')
    
    document.addEventListener('DOMContentLoaded', function () {
        const marketTab = document.getElementById('market-tab');
        const limitTab = document.getElementById('limit-tab');
        const ordTypeInput = document.getElementById('order-type-input');
        
        // Set the default order type to "market" when the page first loads
        ordTypeInput.value = 'market';
    
        // Set the order type to "market" when the Market tab is selected
        marketTab.addEventListener('click', function () {
            ordTypeInput.value = 'market';
        });
    
        // Set the order type to "limit" when the Limit tab is selected
        limitTab.addEventListener('click', function () {
            ordTypeInput.value = 'limit';
        });
    });
        
    // Handle order form submission

    document.getElementById('order-form').onsubmit = async (event) => {
        const token = getAuthToken();

        // Prevent default form submission to handle it with JavaScript
        event.preventDefault();
    
        // Get the button that triggered the submit event
        const submitButton = event.submitter;
        if (!token) {
            alert("You must be logged in to access this.");
            return;
        }


        // declaring variables
        const leadingExchange = document.getElementById('manual-order-form-exchange-input1').value
        const laggingExchange = document.getElementById('manual-order-form-exchange-input2').value
        const marketType1 = document.getElementById('manual-order-form-market-type1').value
        const marketType2 = document.getElementById('manual-order-form-market-type2').value
        const offset1 = document.getElementById('manual-order-form-offset-input1').value
        const offset2 = document.getElementById('manual-order-form-offset-input2').value

        const instrument1 = document.getElementById('manual-order-form-currency-input1').value
        const instrument2 = document.getElementById('manual-order-form-currency-input2').value

        const ordType1 = document.getElementById('manual-order-form-order-type1').value
        const ordType2 = document.getElementById('manual-order-form-order-type2').value

        const sz1 = document.getElementById('manual-order-form-qty-input1').value
        const sz2 = document.getElementById('manual-order-form-qty-input2').value

        const px1 = document.getElementById('manual-order-form-price1').value
        const px2 = document.getElementById('manual-order-form-price2').value

        const username = localStorage.getItem('username')
        const redis_key = localStorage.getItem('key');



        // if (!offset1){
        // }
        // console.log(leadingExchange,laggingExchange,marketType1,marketType2,offset1,offset2,instrument1,instrument2,ordType1,ordType2,sz1,sz2,px1,px2)

        
        const orderData = {
            leadingExchange,
            laggingExchange,
            instrument1,
            instrument2,
            px1,
            px2,
            redis_key,
            username,
            offset1,
            offset2,

            ordType1,
            ordType2,
            sz1,sz2,
            marketType1,marketType2

        };

      


        // Check the value of the submit button to determine which button was clicked
        if (submitButton) {

            if (submitButton.value === "buy") {
                

                if (leadingExchange == laggingExchange){
                    alert('SAME EXCHANGE')
                }
                else{
                    console.log("Buy button clicked. Handling buy action...");
                    let direction1 = 'buy'
                    let direction2 = 'sell'
                    dualOrders(orderData,token,direction1,direction2)
                }
               
              


                // Add your logic for the "Buy" action here
                // Example: Perform AJAX or fetch for the buy action
            } else if (submitButton.value === "sell") {
                if (leadingExchange == laggingExchange && marketType1 == marketType2){
                    alert('SAME EXCHANGE')
                }
                else{
                    console.log("Sell button clicked. Handling sell action...");
                    let direction1 = 'sell'
                    let direction2 = 'buy'
                    dualOrders(orderData,token,direction1,direction2)
                }

                // Add your logic for the "Sell" action here
                // Example: Perform AJAX or fetch for the sell action
            }
        }
    };



    async function dualOrders(orderData,token,direction1,direction2){
        console.log(orderData)
        orderData.px = orderData.px1;
        orderData.instrument = orderData.instrument1;
        orderData.offset = orderData.offset1;
        orderData.ordType = orderData.ordType1
        orderData.sz = parseInt(orderData.sz1)
        orderData.side = direction1

        console.log(orderData)
        let fastapi_folder1 = orderData.leadingExchange + orderData.marketType1
        let fastapi_folder2 = orderData.laggingExchange + orderData.marketType2

        if (orderData.leadingExchange != 'none'){
            const firstOrderPromise = fetch(`http://${hostname}:${exchange_api_port_map.get(fastapi_folder1)}/${fastapi_folder1}/place_order`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(orderData)
            });
            console.log(firstOrderPromise)
            const results = await Promise.allSettled([firstOrderPromise]);

            if (results[0].status === 'fulfilled') {
               
                
                const firstResult = await results[0].value.json();
                console.log(firstResult)

                if (firstResult['error']) {
                    showToast(firstResult['error'])
                    showDone(`${firstResult['error']}`,true)

                } else {
                    firstResult.info['exchange'] = fastapi_folder1
                    showToast(JSON.stringify(firstResult.info))
                    showDone(`${fastapi_folder1}-PLACE ORDER SUCCESS`,false)

                }
            }

        }
        if (orderData.laggingExchange != 'none'){
            let orderData2 = orderData
            orderData2.px = orderData.px2
            orderData2.instrument = orderData.instrument2;
            orderData2.offset = orderData.offset2;
            orderData2.ordType = orderData.ordType2
            console.log(orderData2)
            orderData2.sz = parseInt(orderData.sz2)
            orderData2.side = direction2
            console.log(orderData2)
            const secondOrderPromise = fetch(`http://${hostname}:${exchange_api_port_map.get(fastapi_folder2)}/${fastapi_folder2}/place_order`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(orderData2)
            });

            const results = await Promise.allSettled([secondOrderPromise]);

            if (results[0].status === 'fulfilled') {
               
                
                const firstResult = await results[0].value.json();
                console.log(firstResult)

                if (firstResult['error']) {
                    showToast(firstResult['error'])
                    showDone(`${firstResult['error']}`,true)

                } else {
                    firstResult.info['exchange'] = fastapi_folder2
                    showToast(JSON.stringify(firstResult.info))
                    showDone(`${fastapi_folder2}-PLACE ORDER SUCCESS`,false)

                }
            }
            
        }
        

        
            populatePositions()


    }
    // document.getElementById('order-form').onsubmit = async (event) => {
    //     const token = getAuthToken();
        
    //     if (!token) {
    //         alert("You must be logged in to access this.");
    //         return;
    //     }
    //     console.log("SUBMITTING")
    //     event.preventDefault();
    //     const leadingExchange = document.getElementById('leading-exchange-input').value;
    //     const laggingExchange = document.getElementById('lagging-exchange-input').value;
    //     const instrument = document.getElementById('instrument-input').value;
    //     const ordType = document.getElementById('order-type-input').value;
    //     const instId = document.getElementById('manual-order-form-currency-input').value;
    //     const px1 = document.getElementById('price-input-1').value;
    //     const px2 = document.getElementById('price-input-2').value;
    //     const spread = document.getElementById('spread-input').value;
    //     const sz = document.getElementById('qty-input').value;
    //     const username = localStorage.getItem('username')
    //     const redis_key = localStorage.getItem('key')
    //     const side = event.submitter.value;
    //     const contract_type = document.getElementById('contract-type-input').value

    //     console.log(
    //         leadingExchange,
    //         laggingExchange,
    //         instrument,
    //         ordType,
    //         instId,
    //         px1,
    //         px2,
    //         spread,
    //         sz,
    //         side,
    //         contract_type
    //     )
    //     // Create order object
    //     const orderData = {
    //         leadingExchange,
    //         laggingExchange,
    //         instrument,
    //         ordType,
    //         instId,
    //         px1,
    //         px2,
    //         spread,
    //         sz,
    //         side,
    //         username,
    //         redis_key,
    //         contract_type
    //     };
    //     let exchange_api_port_map = new Map()
    //     exchange_api_port_map.set('okx','5080')
    //     exchange_api_port_map.set('htx','5081')

    //     // Send order data to Redis

    //     try {
    //         // console.log(ordType)
    //         // first check is ordType; second check is leading and lagging; third check is ccy pair
    //         // console.log(orderData)

    //         console.log(orderData, typeof orderData)
            
    //         try {
    //             // Set first order price and prepare first order data
    //             orderData.px = orderData.px1;
    //             const firstOrderPromise = fetch(`http://${hostname}:${exchange_api_port_map.get(leadingExchange)}/${leadingExchange}/${instrument}/place_${ordType}_order`, {
    //                 method: 'POST',
    //                 headers: {
    //                     'Authorization': `Bearer ${token}`,
    //                     'Content-Type': 'application/json',
    //                 },
    //                 body: JSON.stringify(orderData)
    //             });
            
    //             // Prepare second order data
    //             const secondOrderData = { ...orderData }; // Clone the order data
    //             secondOrderData.side = orderData.side === 'buy' ? 'sell' : 'buy';
    //             secondOrderData.px = orderData.px2;
    //             console.log('secondOrderData', secondOrderData);
            
    //             // Set up second order request
    //             const secondOrderPromise = fetch(`http://${hostname}:${exchange_api_port_map.get(laggingExchange)}/${laggingExchange}/${instrument}/place_${ordType}_order`, {
    //                 method: 'POST',
    //                 headers: {
    //                     'Authorization': `Bearer ${token}`,
    //                     'Content-Type': 'application/json',
    //                 },
    //                 body: JSON.stringify(secondOrderData)
    //             });
            
    //             // Run both requests concurrently and wait for both to complete
    //             const results = await Promise.allSettled([firstOrderPromise, secondOrderPromise]);
    //             if (results[0].status === 'fulfilled' ) {
    //                 console.log(results)
    //                 const firstResult = await results[0].value.json();

    //                 if (firstResult.data[0]['errorCode']| firstResult.data[0]['sCode'] == 400){
    //                     console.log("ERROR")
    //                     // showToast('Refresh page','info','exchange','ts','orderId',200,'1039')


    //                     showToast(`Error with first order: ${firstResult.data[0]['sMsg']}`,`${firstResult.data[0]['exchange']}`,`${firstResult.data[0]['ts']}`, `${firstResult.data[0]['ordId']}`,`${firstResult.data[0]['sCode']}`,`${firstResult.data[0]['errorCode']}`);

    //                 } 
    //                 else{
    //                     console.log(firstResult)
    //                     console.log('Response from first server:', firstResult.data);
    //                     showToast(`Success with first order: ${firstResult.data[0]['sMsg']}`,`${firstResult.data[0]['exchange']}`,`${firstResult.data[0]['ts']}`, `${firstResult.data[0]['ordId']}`,`${firstResult.data[0]['sCode']}`,`${firstResult.data[0]['errorCode']}`);

    //                 }

    //             } else {
    //                 console.error('Error with first order:', results[0].reason);
    //                 showToast(`Error with first order: ${firstResult.data[0]['sMsg']}`,`${firstResult.data[0]['exchange']}`,`${firstResult.data[0]['ts']}`, `${firstResult.data[0]['ordId']}`,`${firstResult.data[0]['sCode']}`,`${firstResult.data[0]['errorCode']}`);
    //             }
            
    //             // Handle second order response
    //             if (results[1].status === 'fulfilled') {
    //                 const secondResult = await results[1].value.json();
    //                 console.log(secondResult)
    //                 if (secondResult.data[0]['errorCode']| secondResult.data[0]['sCode'] == 400){
    //                     console.log("ERROR")
    //                     // showToast('Refresh page','info','exchange','ts','orderId',200,'1039')


    //                     showToast(`Error with second order: ${secondResult.data[0]['sMsg']}`,`${secondResult.data[0]['exchange']}`,`${secondResult.data[0]['ts']}`, `${secondResult.data[0]['ordId']}`,`${secondResult.data[0]['sCode']}`,`${secondResult.data[0]['errorCode']}`);
                        
    //                 } 
    //                 else{
    //                     console.log(secondResult)
    //                     console.log('Response from second server:', secondResult.data);
    //                     showToast(`Success with second order: ${secondResult.data[0]['sMsg']}`,`${secondResult.data[0]['exchange']}`,`${secondResult.data[0]['ts']}`, `${secondResult.data[0]['ordId']}`,`${secondResult.data[0]['sCode']}`,`${secondResult.data[0]['errorCode']}`);

    //                 }
                    
                   
    //             } else {
    //                 console.error('Error with second order:', results[1].reason);
    //                 showToast(`Error with second order: ${results[1].reason}`, 4000);
    //             }
    //             populatePositions()
    //         } catch (error) {
    //             console.error('Unexpected error while sending order data:', error);
    //             showToast('An unexpected error occurred while sending order data.', 4000);
    //         }
            
            
    //     } catch (error) {
    //         console.error('Error while sending order data to Redis:', error);
    //     }
    // };

   

});