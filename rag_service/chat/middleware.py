from .metrics import update_metrics

class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Обновляем метрики перед каждым запросом
        update_metrics()
        response = self.get_response(request)
        return response 