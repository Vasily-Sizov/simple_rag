from django.contrib import admin
from django.urls import path, include
from prometheus_client import generate_latest
from django.http import HttpResponse

def metrics_view(request):
    return HttpResponse(
        generate_latest(),
        content_type='text/plain; version=0.0.4; charset=utf-8'
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('chat.urls')),
    path('metrics/', metrics_view, name='prometheus-metrics'),
] 