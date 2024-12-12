document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatMessages = document.getElementById('chat-messages');
    const cardBody = document.querySelector('.card-body');
    const chatUrl = cardBody.dataset.chatUrl;
    
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userInput = document.getElementById('user-input');
        const query = userInput.value.trim();
        
        if (!query) return;

        // Добавляем сообщение пользователя
        addMessage(query, 'user');
        userInput.value = '';

        // Добавляем индикатор загрузки
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        loadingDiv.textContent = 'Генерация ответа...';
        chatMessages.appendChild(loadingDiv);

        try {
            const response = await fetch(chatUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    query: query,
                    use_doc: false
                })
            });

            if (!response.ok) {
                throw new Error(`Ошибка сервера: ${response.status}`);
            }

            const data = await response.json();
            
            // Удаляем индикатор загрузки
            loadingDiv.remove();
            
            // Добавляем ответ бота
            addMessage(data.answer, 'bot');
        } catch (error) {
            loadingDiv.remove();
            addMessage('Произошла ошибка при получении ответа. Попробуйте еще раз.', 'system');
        }
    });

    function addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}); 