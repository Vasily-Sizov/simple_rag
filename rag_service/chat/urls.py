from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload-pdf/', views.upload_pdf, name='upload-pdf'),
    path('chat/', views.chat, name='chat'),
    path('document/', views.document, name='document'),
    path('process-document/', views.process_document, name='process-document'),
    path('monitoring/', views.monitoring, name='monitoring'),
] 