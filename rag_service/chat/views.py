from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.exceptions import RequestAborted
import json
import time
import logging

logger = logging.getLogger('chat')

from .services.document_processor import DocumentProcessor
from .services.mistral_service import MistralService
from .metrics import request_latency, requests_total, update_metrics

doc_processor = DocumentProcessor()
mistral_service = MistralService()

def index(request):
    return render(request, 'chat/chat.html')

def doc_chat(request):
    return render(request, 'chat/doc_chat.html')

@csrf_exempt
def upload_pdf(request):
    if request.method == 'POST' and request.FILES.get('pdf'):
        pdf_file = request.FILES['pdf']
        logger.info(f"Начало обработки PDF файла: {pdf_file.name}")
        doc_processor.process_pdf(pdf_file)
        logger.info(f"PDF файл {pdf_file.name} успешно обработан")
        return JsonResponse({'status': 'success'})
    logger.error("Попытка загрузки PDF файла без файла")
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def chat_response(request):
    if request.method == 'POST':
        try:
            start_time = time.time()
            requests_total.inc()
            
            data = json.loads(request.body)
            query = data.get('query')
            logger.info(f"Получен запрос: {query[:100]}...")
            
            if data.get('use_doc', False):
                logger.debug("Используется режим чата с документом")
                relevant_chunks = doc_processor.get_relevant_chunks(query)
                response = mistral_service.generate_response(query, relevant_chunks)
            else:
                logger.debug("Используется режим простого чата")
                response = mistral_service.generate_simple_response(query)
            
            request_latency.observe(time.time() - start_time)
            update_metrics()
            
            logger.info(f"Ответ сгенерирован за {time.time() - start_time:.2f} сек")
            return JsonResponse(response)
        except RequestAborted:
            logger.warning("Клиент закрыл соединение")
            return JsonResponse({'status': 'aborted'}, status=499)
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {str(e)}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error'}, status=400)

def monitoring(request):
    return render(request, 'chat/monitoring.html')

def document(request):
    return render(request, 'chat/document.html')

@csrf_exempt
def process_document(request):
    if request.method == 'POST' and request.FILES.get('pdf'):
        pdf_file = request.FILES['pdf']
        chunks = doc_processor.process_pdf(pdf_file)
        return JsonResponse({
            'status': 'success',
            'chunks': chunks
        })
    return JsonResponse({'status': 'error'}, status=400) 