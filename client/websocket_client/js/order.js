// Function to handle Buy action
function buy(exchange, ccy) {
    const price = currencyMap[`${exchange}_${ccy}`]?.lastPrice;
    const size = currencyMap[`${exchange}_${ccy}`]?.lastSize;

    if (price && size) {
        alert(`Buying ${size} of ${ccy} at ${price} on ${exchange}`);
        // Here you would implement the actual order logic (e.g., calling an API)
    } else {
        alert("Price or Size is not available.");
    }
}

// Function to handle Sell action
function sell(exchange, ccy) {
    const price = currencyMap[`${exchange}_${ccy}`]?.lastPrice;
    const size = currencyMap[`${exchange}_${ccy}`]?.lastSize;

    if (price && size) {
        alert(`Selling ${size} of ${ccy} at ${price} on ${exchange}`);
        // Here you would implement the actual order logic (e.g., calling an API)
    } else {
        alert("Price or Size is not available.");
    }
}
