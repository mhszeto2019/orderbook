const hostname = window.location.hostname;

document.addEventListener('DOMContentLoaded', () => {
    function getAuthToken() {
        return localStorage.getItem('jwt_token'); // You may use sessionStorage instead if preferred
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
   
    showToast('Refresh page','exchange','ts',null,400,'undefined')
    
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
        
        if (!token) {
            alert("You must be logged in to access this.");
            return;
        }
        console.log("SUBMITTING")
        event.preventDefault();
        const leadingExchange = document.getElementById('leading-exchange-input').value;
        const laggingExchange = document.getElementById('lagging-exchange-input').value;
        const instrument = document.getElementById('instrument-input').value;
        const ordType = document.getElementById('order-type-input').value;
        const instId = document.getElementById('manual-order-form-currency-input').value;
        const px1 = document.getElementById('price-input-1').value;
        const px2 = document.getElementById('price-input-2').value;
        const spread = document.getElementById('spread-input').value;
        const sz = document.getElementById('qty-input').value;
        const username = localStorage.getItem('username')
        const redis_key = localStorage.getItem('key')
        const side = event.submitter.value;
        const contract_type = document.getElementById('contract-type-input').value

        console.log(
            leadingExchange,
            laggingExchange,
            instrument,
            ordType,
            instId,
            px1,
            px2,
            spread,
            sz,
            side,
            contract_type
        )
        // Create order object
        const orderData = {
            leadingExchange,
            laggingExchange,
            instrument,
            ordType,
            instId,
            px1,
            px2,
            spread,
            sz,
            side,
            username,
            redis_key,
            contract_type
        };
        let exchange_api_port_map = new Map()
        exchange_api_port_map.set('okx','5080')
        exchange_api_port_map.set('htx','5081')

        // Send order data to Redis

        try {
            // console.log(ordType)
            // first check is ordType; second check is leading and lagging; third check is ccy pair
            // console.log(orderData)

            console.log(orderData, typeof orderData)
            
            try {
                // Set first order price and prepare first order data
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
                console.log('secondOrderData', secondOrderData);
            
                // Set up second order request
                const secondOrderPromise = fetch(`http://${hostname}:${exchange_api_port_map.get(laggingExchange)}/${laggingExchange}/${instrument}/place_${ordType}_order`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(secondOrderData)
                });
            
                // Run both requests concurrently and wait for both to complete
                const results = await Promise.allSettled([firstOrderPromise, secondOrderPromise]);
                if (results[0].status === 'fulfilled' ) {
                    console.log(results)
                    const firstResult = await results[0].value.json();

                    if (firstResult.data[0]['errorCode']| firstResult.data[0]['sCode'] == 400){
                        console.log("ERROR")
                        // showToast('Refresh page','info','exchange','ts','orderId',200,'1039')


                        showToast(`Error with first order: ${firstResult.data[0]['sMsg']}`,`${firstResult.data[0]['exchange']}`,`${firstResult.data[0]['ts']}`, `${firstResult.data[0]['ordId']}`,`${firstResult.data[0]['sCode']}`,`${firstResult.data[0]['errorCode']}`);

                    } 
                    else{
                        console.log(firstResult)
                        console.log('Response from first server:', firstResult.data);
                        showToast(`Success with first order: ${firstResult.data[0]['sMsg']}`,`${firstResult.data[0]['exchange']}`,`${firstResult.data[0]['ts']}`, `${firstResult.data[0]['ordId']}`,`${firstResult.data[0]['sCode']}`,`${firstResult.data[0]['errorCode']}`);

                    }

                } else {
                    console.error('Error with first order:', results[0].reason);
                    showToast(`Error with first order: ${firstResult.data[0]['sMsg']}`,`${firstResult.data[0]['exchange']}`,`${firstResult.data[0]['ts']}`, `${firstResult.data[0]['ordId']}`,`${firstResult.data[0]['sCode']}`,`${firstResult.data[0]['errorCode']}`);
                }
            
                // Handle second order response
                if (results[1].status === 'fulfilled') {
                    const secondResult = await results[1].value.json();
                    console.log(secondResult)
                    if (secondResult.data[0]['errorCode']| secondResult.data[0]['sCode'] == 400){
                        console.log("ERROR")
                        // showToast('Refresh page','info','exchange','ts','orderId',200,'1039')


                        showToast(`Error with second order: ${secondResult.data[0]['sMsg']}`,`${secondResult.data[0]['exchange']}`,`${secondResult.data[0]['ts']}`, `${secondResult.data[0]['ordId']}`,`${secondResult.data[0]['sCode']}`,`${secondResult.data[0]['errorCode']}`);
                        
                    } 
                    else{
                        console.log(secondResult)
                        console.log('Response from second server:', secondResult.data);
                        showToast(`Success with second order: ${secondResult.data[0]['sMsg']}`,`${secondResult.data[0]['exchange']}`,`${secondResult.data[0]['ts']}`, `${secondResult.data[0]['ordId']}`,`${secondResult.data[0]['sCode']}`,`${secondResult.data[0]['errorCode']}`);

                    }
                    
                   
                } else {
                    console.error('Error with second order:', results[1].reason);
                    showToast(`Error with second order: ${results[1].reason}`, 4000);
                }
                populatePositions()
            } catch (error) {
                console.error('Unexpected error while sending order data:', error);
                showToast('An unexpected error occurred while sending order data.', 4000);
            }
            
            
        } catch (error) {
            console.error('Error while sending order data to Redis:', error);
        }
    };

   

});