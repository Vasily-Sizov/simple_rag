from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import RequestAborted
import json
import time

from .services.document_processor import DocumentProcessor
from .services.saiga_service import SaigaService
from .metrics import request_latency, requests_total, update_metrics

doc_processor = DocumentProcessor()
saiga_service = SaigaService()

def index(request):
    return render(request, 'chat/index.html')

@csrf_exempt
def upload_pdf(request):
    if request.method == 'POST' and request.FILES.get('pdf'):
        pdf_file = request.FILES['pdf']
        doc_processor.process_pdf(pdf_file)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def chat(request):
    if request.method == 'POST':
        try:
            start_time = time.time()
            requests_total.inc()
            
            data = json.loads(request.body)
            query = data.get('query')
            
            relevant_chunks = doc_processor.get_relevant_chunks(query)
            response = saiga_service.generate_response(query, relevant_chunks)
            
            request_latency.observe(time.time() - start_time)
            update_metrics()
            
            return JsonResponse(response)
        except RequestAborted:
            print("Клиент закрыл соединение")
            return JsonResponse({'status': 'aborted'}, status=499)  # 499 - Client Closed Request
        except Exception as e:
            print(f"Ошибка при обработке запроса: {e}")
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