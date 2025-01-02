
// update currency options on the MANUAL order side - when users click swap or futures, the currency available in each instrument will be populated
// function updateCurrencyOptions() {
//     const instrumentInput = document.getElementById('instrument-input');
//     const currencyInput = document.getElementById('manual-order-form-currency-input');
//     const contractTypeContainer = document.getElementById('contract-type-container');

//     // Clear existing options
//     currencyInput.innerHTML = '<option value="">Select Currency Pair</option>';

//     // Add options based on the selected instrument
//     if (instrumentInput.value === 'futures') {
//         const futuresOptions = [
//             { value: 'BTC', text: 'BTC' },
//             // { value: 'ETH-USD-0425', text: 'ETH-USD-0425' },
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
//             // { value: 'BTC-USD-0328', text: 'BTC-USD-0328' },
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

// // update currency options on the ALGO order side - when users click swap or futures, the currency available in each instrument will be populated
// function updateCurrencyOptionsAlgoSide() {
//     const instrumentInput = document.getElementById('new-algo-instrument');
//     const currencyInput = document.getElementById('new-algo-ccy');
//     const contractTypeContainer = document.getElementById('new-algo-contract-type-container');

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


function updateCurrencyOptionsGeneral(instrumentInputId, currencyInputId, contractTypeContainerId) {
    const instrumentInput = document.getElementById(instrumentInputId);
    const currencyInput = document.getElementById(currencyInputId);
    const contractTypeContainer = document.getElementById(contractTypeContainerId);

    // Clear existing options
    currencyInput.innerHTML = '<option value="">Select Currency Pair</option>';
    
    // Add options based on the selected instrument
    if (instrumentInput.value === 'futures') {
        const futuresOptions = [
            { value: 'BTC', text: 'BTC' },
        ];
        futuresOptions.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option.value;
            opt.textContent = option.text;
            currencyInput.appendChild(opt);
        });

        // Show Contract Type field
        contractTypeContainer.style.display = 'block';
    } else if (instrumentInput.value === 'swap') {
        const defaultOptions = [
            { value: 'BTC-USD-SWAP', text: 'BTC-USD-SWAP' },
        ];
        defaultOptions.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option.value;
            opt.textContent = option.text;
            currencyInput.appendChild(opt);
        });

        // Hide Contract Type field
        contractTypeContainer.style.display = 'none';
    }
}



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
