


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

    // POTENTIALLY ADD EXCHANGE TYPE AND MARKET TYPE TO DERIVE CURRENCIES PRESENT

      const currenciesSpot = ['BTC-USD', 'ETH-USD'];
      const currenciesPerp = ['BTC-USDT-SWAP', 'ETH-USDT-SWAP'];

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

      // Update currency options based on market type
      populateCurrencies('manual-order-form-currency-input1', marketType1);
      populateCurrencies('manual-order-form-currency-input2', marketType2);
    }

    // Event listeners for changes in market type
    document.getElementById('manual-order-form-market-type1').addEventListener('change', updateCurrencyOptions);
    document.getElementById('manual-order-form-market-type2').addEventListener('change', updateCurrencyOptions);

    // Initial population of currency options
    updateCurrencyOptions();
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
