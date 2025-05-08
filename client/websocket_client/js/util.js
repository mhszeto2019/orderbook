


// function updateCurrencyOptionsGeneral(instrumentInputId, currencyInputId, contractTypeContainerId) {
//     const instrumentInput = document.getElementById(instrumentInputId);
//     const currencyInput = document.getElementById(currencyInputId);
//     const contractTypeContainer = document.getElementById(contractTypeContainerId);

//     // Clear existing options
//     currencyInput.innerHTML = '<option value="">Select Currency Pair</option>';
    
//     // Add options based on the selected instrument
//     if (instrumentInput.value === 'futures') {
//         const futuresOptions = [
//             { value: 'BTC', text: 'BTC' },
//         ];
//         futuresOptions.forEach(option => {
//             const opt = document.createElement('option');
//             opt.value = option.value;
//             opt.textContent = option.text;
//             currencyInput.appendChild(opt);
//         });

//         // Show Contract Type field
//         contractTypeContainer.style.display = 'block';
//     } else if (instrumentInput.value === 'swap') {
//         const defaultOptions = [
//             { value: 'BTC-USD-SWAP', text: 'BTC-USD-SWAP' },
//         ];
//         defaultOptions.forEach(option => {
//             const opt = document.createElement('option');
//             opt.value = option.value;
//             opt.textContent = option.text;
//             currencyInput.appendChild(opt);
//         });

//         // Hide Contract Type field
//         contractTypeContainer.style.display = 'none';
//     }
// }


// CHANGING CURRENCY BASED ON PERP AND SPOT
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the tooltips
    var tooltipTriggerList = Array.from(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Select currency based on exchange and market type
    function updateCurrencyOptions() {

      const marketType1 = document.getElementById('manual-order-form-market-type1').value;
      const marketType2 = document.getElementById('manual-order-form-market-type2').value;


      const orderTypeOptions = {
        spot:[
            {value: 'limit' , text:'LIMIT'},
            {value: 'market' , text:'MARKET'}
        ],
        perp:[
            {value: 'limit' , text:'LIMIT'},
            {value: 'counterparty1' , text:'COUNTERPARTY-1'},
            {value: 'counterparty5' , text:'COUNTERPARTY-5'},
            {value: 'queue1' , text:'QUEUE-1'},
            {value: 'market' , text:'MARKET'}
        ]
    }
    
    // POTENTIALLY ADD EXCHANGE TYPE AND MARKET TYPE TO DERIVE CURRENCIES PRESENT

      const currenciesSpot = ['BTC-USDT', 'BTC-USDC','ETH-USD'];
      const currenciesPerp = ['BTC-USD-SWAP','BTC-USDT-SWAP', 'ETH-USDT-SWAP'];

      // Function to update currency dropdowns based on market type
      function populateCurrencies(selectId, marketType) {
        const currencySelect = document.getElementById(selectId);
        currencySelect.innerHTML = '';  // Clear previous options
        const options = marketType === 'spot' ? currenciesSpot : currenciesPerp;

        options.forEach(currency => {
          const option = document.createElement('option');
          option.value = currency;
          option.textContent = currency;
          currencySelect.appendChild(option);
        });


      }
      function populateOrderType(selectId,marketType){
        const orderTypeSelect = document.getElementById(selectId)

        orderTypeSelect.innerHTML=''
        const orderTypeOptionsArr = orderTypeOptions[marketType] || [];
        orderTypeOptionsArr.forEach(opt => {
            const optionField = document.createElement('option');
            optionField.value = opt.value;
            optionField.textContent = opt.text;
            orderTypeSelect.appendChild(optionField);
        });
      }
       



    

    



      // Update currency options based on market type
      populateCurrencies('manual-order-form-currency-input1', marketType1);
      populateCurrencies('manual-order-form-currency-input2', marketType2);
      populateOrderType('manual-order-form-order-type1', marketType1);
      populateOrderType('manual-order-form-order-type2', marketType2);
      
    }

    // Event listeners for changes in market type
    document.getElementById('manual-order-form-market-type1').addEventListener('change', updateCurrencyOptions);
    document.getElementById('manual-order-form-market-type2').addEventListener('change', updateCurrencyOptions);

    // Initial population of currency options
    updateCurrencyOptions();
  });



// CHANGING PRICE FIELD BASED ON ORDER TYPE
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the tooltips
    var tooltipTriggerList = Array.from(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Function to hide price fields
    function hidePriceFields() {
        document.getElementById('manual-order-form-price-field1').classList.add('hidden');
        document.getElementById('manual-order-form-price-field2').classList.add('hidden');
    }
  
    // Function to show price fields
    function showPriceFields() {
        document.getElementById('manual-order-form-price-field1').classList.remove('hidden');
        document.getElementById('manual-order-form-price-field2').classList.remove('hidden');
    }

 
    const orderType1 = document.getElementById('manual-order-form-order-type1')
    const orderType2 = document.getElementById('manual-order-form-order-type2')
    let priceField1 = document.getElementById('manual-order-form-price-field1')
    let priceField2 = document.getElementById('manual-order-form-price-field2')

    const hiddenOrderTypes = ['market', 'counterparty1', 'counterparty5','queue1'];

    if (hiddenOrderTypes.includes(orderType1.value)) {
        priceField1.classList.add('hidden');
    } else {
        priceField1.classList.remove('hidden');
    }

    if (hiddenOrderTypes.includes(orderType2.value)) {
      priceField2.classList.add('hidden');
    } else {
        priceField2.classList.remove('hidden');
    }


    // if (orderType2.value == 'market'){
    //     priceField2.classList.add('hidden');

    // }
    // else if (orderType2.value == 'counterparty1'){
    //   priceField2.classList.add('hidden');
    // }
    // else{
    //     priceField2.classList.remove('hidden');

    // }

    // Select currency based on exchange and market type
    function updatePriceField() {
        const orderType1 = document.getElementById('manual-order-form-order-type1')
        const orderType2 = document.getElementById('manual-order-form-order-type2')
        let priceField1 = document.getElementById('manual-order-form-price-field1')
        let priceField2 = document.getElementById('manual-order-form-price-field2')
        console.log(orderType1.value)

        const hiddenOrderTypes = ['market', 'counterparty1', 'counterparty5','queue1'];

        if (hiddenOrderTypes.includes(orderType1.value)) {
            priceField1.classList.add('hidden');
        } else {
            priceField1.classList.remove('hidden');
        }
        if (hiddenOrderTypes.includes(orderType2.value)) {
          priceField2.classList.add('hidden');
        } else {
            priceField2.classList.remove('hidden');
        }

        // if (orderType2.value == 'market'){
        //     priceField2.classList.add('hidden');

        // }
        // else if (orderType2.value == 'counterparty1'){
        //   priceField2.classList.add('hidden');
        // }
        // else{
        //     priceField2.classList.remove('hidden');

        // }
        

    }

 
    document.getElementById('manual-order-form-order-type1').addEventListener('change', updatePriceField);
    document.getElementById('manual-order-form-order-type2').addEventListener('change', updatePriceField);

  });



// CHANGING OFFSET FIELD BASED ON EXCHANGE TYPE
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the tooltips
    // var tooltipTriggerList = Array.from(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    // var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    //   return new bootstrap.Tooltip(tooltipTriggerEl);
    // });

    
 
    // const orderType1 = document.getElementById('manual-order-form-order-type1')
    // const orderType2 = document.getElementById('manual-order-form-order-type2')
    // let priceField1 = document.getElementById('manual-order-form-price-field1')
    // let priceField2 = document.getElementById('manual-order-form-price-field2')
    // if (orderType1.value == 'market'){
    //     priceField1.classList.add('hidden');

    // }
    // else{
    //     priceField1.classList.remove('hidden');

    // }

    // if (orderType2.value == 'market'){
    //     priceField2.classList.add('hidden');

    // }
    // else{
    //     priceField2.classList.remove('hidden');

    // }

      // Select currency based on exchange and market type
      function updateOffsetField() {

        const exchangeType1 = document.getElementById('manual-order-form-exchange-input1').value;
        const exchangeType2 = document.getElementById('manual-order-form-exchange-input2').value;
        
  
      // POTENTIALLY ADD EXCHANGE TYPE AND MARKET TYPE TO DERIVE CURRENCIES PRESENT
  
        const offsetTypes = ['open', 'close'];
  
        // Function to update currency dropdowns based on market type
        function populateOffsets(selectId, exchangeType) {
            const offsetSelect = document.getElementById(selectId);
            offsetSelect.innerHTML = '';  // Clear previous options
            const options = exchangeType === 'htx' ? offsetTypes : [];
            if (options){
                options.forEach(offset => {
                    const option = document.createElement('option');
                    option.value = offset;
                    option.textContent = offset;
                    offsetSelect.appendChild(option);
                });
            }
          
        }
  
        // Update currency options based on market type
        populateOffsets('manual-order-form-offset-input1', exchangeType1);
        populateOffsets('manual-order-form-offset-input2', exchangeType2);
      }
  
      // Event listeners for changes in market type
      document.getElementById('manual-order-form-exchange-input1').addEventListener('change', updateOffsetField);
      document.getElementById('manual-order-form-exchange-input2').addEventListener('change', updateOffsetField);
  
      // Initial population of currency options
      updateOffsetField();
});


 
// Setting algo type name - triggered in modal when we selectn new algo type
  function setnewAlgoType(element) {
    // Get the value stored in the data-value attribute of the clicked <a> tag
    const algoType = element.getAttribute('data-value');

    // Update the dropdown button text to show the selected value
    const dropdownButton = document.getElementById('new-algo-algoType-button');
    dropdownButton.innerHTML = algoType; // Change button text to the selected algo type

    // If you want to update an input field with the selected value:
    const algoTypeInput = document.getElementById('new-algo-type');
    algoTypeInput.value = algoType;

}
