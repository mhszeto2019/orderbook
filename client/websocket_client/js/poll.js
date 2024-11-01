    // Function to fetch HTX funding rates using API
    function fetchFundingRateFromAPI(exchange, ccy) {
        const apiUrl = `http://localhost:5011/get_funding_rate?exchange=${exchange}&ccy=${ccy}`;

        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                const { funding_rate, fundingTime } = data;
                updateFundingRate(exchange, ccy, funding_rate, fundingTime);
            })
            .catch(error => console.error('Error fetching funding rate from API:', error));
    }

    // Poll HTX funding rates every 60 seconds
    function pollHTXFundingRates() {
        fixedOrder.forEach(pair => {
            if (pair.exchange === 'htx') {
                fetchFundingRateFromAPI(pair.exchange, pair.ccy);
            }
        });

        setTimeout(pollHTXFundingRates, 60000);
    }

    // Start polling HTX funding rates
    pollHTXFundingRates();

    function handlePriceUpdate(event, message) {
        if (event.startsWith('okx_live_price_') || event.startsWith('htx_live_price_')) {
            try {
                const { exchange, ccy, lastPrice, lastSize, ts, channel } = JSON.parse(message.data);
                updatePriceData(exchange, ccy, lastPrice, lastSize, ts, channel);
            } catch (error) {
                console.error("Error parsing price update:", error);
            }
        }
    }