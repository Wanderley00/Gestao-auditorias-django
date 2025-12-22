from django.urls import path
from . import views

app_name = 'planos_de_acao'

urlpatterns = [
    path('api/forum/<int:forum_id>/mensagens/',
         views.api_listar_mensagens, name='api_listar_mensagens'),
    path('api/forum/<int:forum_id>/enviar/',
         views.api_enviar_mensagem, name='api_enviar_mensagem'),

    path('api/mensagem/<int:mensagem_id>/editar/',
         views.api_editar_mensagem, name='api_editar_mensagem'),
    path('api/mensagem/<int:mensagem_id>/deletar/',
         views.api_deletar_mensagem, name='api_deletar_mensagem'),
]
