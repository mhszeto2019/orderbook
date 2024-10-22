const order_management_sockets = {
    okx_open_orders: io('http://localhost:5021', {
        transports: ['websocket'],
        // debug: false // Disable debug logging
    }),

};

// Optimize connection logging
Object.entries(order_management_sockets).forEach(([name, socket]) => {
    socket.on('connect', () => console.log(`Connected to ${name} WebSocket`));
});

order_management_sockets.okx_open_orders.onAny((event, message) => handlePriceUpdate(event, message));


function handlePriceUpdate(event,message){
    console.log(event,message)
}