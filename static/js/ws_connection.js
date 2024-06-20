document.addEventListener('DOMContentLoaded', (event) => {
    const button = document.getElementById('generateTextButton');
    const socket = new WebSocket('ws://127.0.0.1:8000/ws');
    if (button) {
        button.addEventListener('click', (event) => {
            event.preventDefault();
            document.querySelector('.jumbotron .container .text-to-change-1').innerHTML = "";
            document.querySelector('.jumbotron .container .text-to-change-2').innerHTML = "";
            // Listen for messages
            prompt = document.getElementById("prompt").value;
            console.log('here is the prompt : ', prompt)
            socket.send(prompt)
            socket.addEventListener('message', (event) => {
                console.log('Message from server ', event.data);
                // Update the content of the div block
                const data = JSON.parse(event.data);
                if (data.channel_1) {
                    document.querySelector('.jumbotron .container .text-to-change-1').innerHTML += data.channel_1;
                }
                if (data.channel_2) {
                    document.querySelector('.jumbotron .container .text-to-change-2').innerHTML += data.channel_2;
                }            });
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
        console.error('Button with ID "generateTextButton" not found.');
    }
});