document.addEventListener('DOMContentLoaded', function() {
    const pdfForm = document.getElementById('pdf-upload-form');
    const chatForm = document.getElementById('chat-form');
    const chatMessages = document.getElementById('chat-messages');
    const uploadStatus = document.getElementById('upload-status');
    
    let isPdfUploaded = false;

    // Обработка загрузки PDF
    pdfForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        const pdfFile = document.getElementById('pdf-file').files[0];
        formData.append('pdf', pdfFile);

        try {
            uploadStatus.className = 'alert alert-info';
            uploadStatus.textContent = 'Загрузка и обработка файла...';
            uploadStatus.classList.remove('d-none');

            const response = await fetch('/upload-pdf/', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                uploadStatus.className = 'alert alert-success';
                uploadStatus.textContent = 'Файл успешно загружен и обработан!';
                isPdfUploaded = true;
            } else {
                throw new Error('Ошибка загрузки файла');
            }
        } catch (error) {
            uploadStatus.className = 'alert alert-danger';
            uploadStatus.textContent = 'Ошибка при загрузке файла. Попробуйте еще раз.';
        }
    });

    // Обработка отправки сообщения
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!isPdfUploaded) {
            alert('Пожалуйста, сначала загрузите PDF файл');
            return;
        }

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
            const response = await fetch('/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    query: query
                })
            });

            if (!response.ok) {
                if (response.status === 499) {
                    throw new Error('Запрос был прерван. Попробуйте еще раз.');
                }
                throw new Error(`Ошибка сервера: ${response.status}`);
            }

            const data = await response.json();
            
            // Удаляем индикатор загрузки
            loadingDiv.remove();
            
            // Добавляем контекст и ответ бота
            addMessage(data.instruction, 'instruction', 'Инструкция');
            addMessage(data.context.join('\n'), 'context', 'Контекст');
            addMessage(data.question, 'user-question', 'Вопрос');
            addMessage(data.answer, 'bot', 'Ответ');
        } catch (error) {
            loadingDiv.remove();
            addMessage('Произошла ошибка при получении ответа. Попробуйте еще раз.', 'system');
        }
    });

    function addMessage(text, type, label) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        // Добавляем заголовок блока
        if (label) {
            const labelDiv = document.createElement('div');
            labelDiv.className = 'message-label';
            labelDiv.textContent = label;
            messageDiv.appendChild(labelDiv);
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text;
        messageDiv.appendChild(contentDiv);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}); 