# ativos/urls.py

from django.urls import path
from . import views

app_name = 'ativos'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_ativos, name='dashboard'),
    
    # Categorias
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/criar/', views.criar_categoria, name='criar_categoria'),
    path('categorias/<int:pk>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:pk>/deletar/', views.deletar_categoria, name='deletar_categoria'),
    
    # Marcas
    path('marcas/', views.lista_marcas, name='lista_marcas'),
    path('marcas/criar/', views.criar_marca, name='criar_marca'),
    path('marcas/<int:pk>/editar/', views.editar_marca, name='editar_marca'),
    path('marcas/<int:pk>/deletar/', views.deletar_marca, name='deletar_marca'),
    
    # Modelos
    path('modelos/', views.lista_modelos, name='lista_modelos'),
    path('modelos/criar/', views.criar_modelo, name='criar_modelo'),
    path('modelos/<int:pk>/editar/', views.editar_modelo, name='editar_modelo'),
    path('modelos/<int:pk>/deletar/', views.deletar_modelo, name='deletar_modelo'),
    
    # Ativos
    path('ativos/', views.lista_ativos, name='lista_ativos'),
    path('ativos/criar/', views.criar_ativo, name='criar_ativo'),
    path('ativos/<int:pk>/editar/', views.editar_ativo, name='editar_ativo'),
    path('ativos/<int:pk>/deletar/', views.deletar_ativo, name='deletar_ativo'),
    
    # AJAX
    path('ajax/modelos-por-marca/', views.get_modelos_por_marca, name='get_modelos_por_marca'),
]