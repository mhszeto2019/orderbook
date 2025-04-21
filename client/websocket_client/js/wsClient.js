
        const socket = new WebSocket("ws://localhost:8000/ws");

        socket.onopen = () => {
            console.log("Connected to server");
        };

        socket.onmessage = (event) => {
            const msg = document.createElement("li");
            msg.textContent = event.data;
            document.getElementById("messages").appendChild(msg);
        };

        socket.onclose = () => {
            console.log("Disconnected from server");
        };

        socket.onerror = (error) => {
            console.log("WebSocket Error: ", error);
        };

        function sendMessage() {
            const input = document.getElementById("messageInput");
            const message = input.value;
            socket.send(message);  // Send the message to the server
            input.value = "";  // Clear input field
        }
 