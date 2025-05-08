const currencyOptions = {
    spot: [
        { value: 'BTC-USDT', text: 'BTC-USDT' },
        { value: 'BTC-USDC', text: 'BTC-USDC' },
        { value: 'BTC-USD', text: 'BTC-USD' }
    ],
    perp: [
        { value: '', text: '--Not Selected--' },
        { value: 'BTC/USD:BTC', text: 'BTC-USD-SWAP' },
        { value: 'BTC/USDT:USDT', text: 'BTC-USDT-SWAP' },
        { value: 'ETH/USD:ETH', text: 'ETH-USD-SWAP' },


    ],
    futures: [
        { value: 'BTC-USD-FUT', text: 'BTC-USD-FUT' },
        { value: 'BTC-USDT-FUT', text: 'BTC-USDT-FUT' }
    ]
};

function updateCurrencyOptions() {
    const marketType = document.getElementById('market-type').value;
    const currencySelect = document.getElementById('fundingrate-currency-input');
    currencySelect.innerHTML = ''; // Clear old options

    const options = currencyOptions[marketType] || [];
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.text;
        currencySelect.appendChild(option);
        if (opt.value == "BTC/USD:BTC") {
            option.selected = true;
        }
    });
    
}



function updateCurrencyOptionsOrderbook1() {
    const marketType = document.getElementById('market-type-orderbook1').value;
    const currencySelect = document.getElementById('currency-input-orderbook1');
    currencySelect.innerHTML = ''; // Clear old options

    const options = currencyOptions[marketType] || [];
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.text;
        currencySelect.appendChild(option);
    });

   

}


function updateCurrencyOptionsOrderbook2() {


    const marketType = document.getElementById('market-type-orderbook2').value;
    const currencySelect = document.getElementById('currency-input-orderbook2');
    currencySelect.innerHTML = ''; // Clear old options
    const options = currencyOptions[marketType] || [];
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.text;
        currencySelect.appendChild(option);
        // if (opt.value == "BTC-USD-SWAP") {
        //     option.selected = true;
        //     console.log("SELECTIONEDD")
        //     console.log(currencySelect.value)
        // }
    });
    
}

// Initialize with default market type (spot)
document.addEventListener('DOMContentLoaded', updateCurrencyOptions);
document.addEventListener('DOMContentLoaded', updateCurrencyOptionsOrderbook1);
document.addEventListener('DOMContentLoaded', updateCurrencyOptionsOrderbook2);



function populateFundingRate() {
    const marketType = document.getElementById('market-type').value;
    const selectedCurrency = document.getElementById('fundingrate-currency-input').value;

}

document.addEventListener('DOMContentLoaded', function () {
    const marketTypeSelect = document.getElementById('market-type-input');
    const currencySelect = document.getElementById('fundingrate-currency-input');

    if (marketTypeSelect) {
        marketTypeSelect.addEventListener('change', populateFundingRate);
    }

    if (currencySelect) {
        currencySelect.addEventListener('change', populateFundingRate);
    }
});