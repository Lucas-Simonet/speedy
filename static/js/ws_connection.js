document.addEventListener('DOMContentLoaded', (event) => {
    const button = document.getElementById('learnMoreButton');
    if (button) {
        button.addEventListener('click', (event) => {
            event.preventDefault();
            document.querySelector('.jumbotron .container .text-to-change').innerHTML = "";
            // Initialize WebSocket on button click
            const socket = new WebSocket('ws://127.0.0.1:8000/ws');
            // Connection opened
            socket.addEventListener('open', (event) => {
                console.log('WebSocket is open now.');
                // Send a message to the server
                socket.send('Button clicked');
            });
            // Listen for messages
            socket.addEventListener('message', (event) => {
                console.log('Message from server ', event.data);
                // Update the content of the div block
                document.querySelector('.jumbotron .container .text-to-change').innerHTML += event.data;
            });
            // Handle connection close
            socket.addEventListener('close', (event) => {
                console.log('WebSocket is closed now.');
            });
            // Handle errors
            socket.addEventListener('error', (event) => {
                console.error('WebSocket error observed:', event);
            });
        });
    } else {
        console.error('Button with ID "learnMoreButton" not found.');
    }
});