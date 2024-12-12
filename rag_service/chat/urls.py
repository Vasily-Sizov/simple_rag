from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('doc-chat/', views.doc_chat, name='doc-chat'),
    path('chat-response/', views.chat_response, name='chat-response'),
    path('upload-pdf/', views.upload_pdf, name='upload-pdf'),
    path('document/', views.document, name='document'),
    path('process-document/', views.process_document, name='process-document'),
    path('monitoring/', views.monitoring, name='monitoring'),
] 