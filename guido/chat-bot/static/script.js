document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const aiSelector = document.getElementById('ai-select');

    // Saludo automático
    setTimeout(() => {
        displayMessage("¡Hola! Soy tu asistente con múltiples IAs. Usa el selector para elegir qué IA quieres usar.", 'bot-message');
    }, 500);

    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendMessage();
    });

    sendBtn.addEventListener('click', sendMessage);

    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;
        
        // Mostrar mensaje del usuario con IA seleccionada
        const selectedAI = aiSelector.value;
        displayMessage(`${message} [IA: ${selectedAI}]`, 'user-message');
        userInput.value = '';
        
        // Enviar a Flask con la IA seleccionada
        fetch('/get_response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `message=${encodeURIComponent(message)}&ai_type=${selectedAI}`
        })
        .then(response => response.json())
        .then(data => {
            displayMessage(data.response, 'bot-message');
        })
        .catch(error => {
            console.error('Error:', error);
            displayMessage("Error al conectar con la IA", 'bot-message');
        });
    }

    function displayMessage(message, className) {
        const msgElement = document.createElement('div');
        msgElement.classList.add('message', className);
        msgElement.textContent = message;
        chatBox.appendChild(msgElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});