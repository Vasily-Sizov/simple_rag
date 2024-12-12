document.addEventListener('DOMContentLoaded', function() {
    const pdfForm = document.getElementById('pdf-upload-form');
    const chunksContainer = document.getElementById('chunks-container');
    const uploadStatus = document.getElementById('upload-status');

    pdfForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        const pdfFile = document.getElementById('pdf-file').files[0];
        formData.append('pdf', pdfFile);

        try {
            uploadStatus.className = 'alert alert-info';
            uploadStatus.textContent = 'Загрузка и обработка файла...';
            uploadStatus.classList.remove('d-none');

            const response = await fetch('/process-document/', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                uploadStatus.className = 'alert alert-success';
                uploadStatus.textContent = 'Файл успешно загружен и обработан!';
                
                // Отображаем чанки
                displayChunks(data.chunks);
            } else {
                throw new Error('Ошибка загрузки файла');
            }
        } catch (error) {
            uploadStatus.className = 'alert alert-danger';
            uploadStatus.textContent = 'Ошибка при загрузке файла. Попробуйте еще раз.';
        }
    });

    function displayChunks(chunks) {
        chunksContainer.innerHTML = '';
        chunks.forEach((chunk, index) => {
            const chunkDiv = document.createElement('div');
            chunkDiv.className = 'chunk-item';
            const escapedChunk = chunk.replace(/</g, '&lt;').replace(/>/g, '&gt;');
            chunkDiv.innerHTML = `
                <div class="chunk-number">Чанк #${index + 1}</div>
                <div class="chunk-content">${escapedChunk}</div>
            `;
            chunksContainer.appendChild(chunkDiv);
        });
    }
}); 