# usuarios/urls.py

from django.urls import path
from . import views
from .views import CustomAuthToken

app_name = 'usuarios'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_usuarios, name='dashboard'),

    # Usuários
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/criar/', views.criar_usuario, name='criar_usuario'),
    path('usuarios/<int:pk>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:pk>/deletar/',
         views.deletar_usuario, name='deletar_usuario'),
    path('usuarios/<int:pk>/alterar-senha/',
         views.alterar_senha_usuario, name='alterar_senha_usuario'),

    # Grupos
    path('grupos/', views.lista_grupos, name='lista_grupos'),
    path('grupos/criar/', views.criar_grupo, name='criar_grupo'),
    path('grupos/<int:pk>/editar/', views.editar_grupo, name='editar_grupo'),
    path('grupos/<int:pk>/deletar/', views.deletar_grupo, name='deletar_grupo'),

    # AJAX
    path('ajax/verificar-username/',
         views.verificar_username, name='verificar_username'),
    path('ajax/verificar-email/', views.verificar_email, name='verificar_email'),
    path('ajax/toggle-status/<int:pk>/',
         views.toggle_usuario_status, name='toggle_usuario_status'),
    path('ajax/bulk-action/', views.bulk_action_usuarios,
         name='bulk_action_usuarios'),

    # Perfil do usuário
    path('meu-perfil/', views.meu_perfil, name='meu_perfil'),
    path('alterar-senha/', views.alterar_minha_senha, name='alterar_minha_senha'),

]
