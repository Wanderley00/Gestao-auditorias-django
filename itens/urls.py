# itens/urls.py

from django.urls import path
from . import views

app_name = 'itens'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard_itens, name='dashboard'),

    # Itens
    path('', views.lista_itens, name='lista_itens'),
    path('criar/', views.criar_item, name='criar_item'),
    path('<int:pk>/editar/', views.editar_item, name='editar_item'),
    path('<int:pk>/deletar/', views.deletar_item, name='deletar_item'),
    
    # Categorias de Itens
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/criar/', views.criar_categoria, name='criar_categoria'),
    path('categorias/<int:pk>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:pk>/deletar/', views.deletar_categoria, name='deletar_categoria'),

    # Subcategorias de Itens
    path('subcategorias/', views.lista_subcategorias, name='lista_subcategorias'),
    path('subcategorias/criar/', views.criar_subcategoria, name='criar_subcategoria'),
    path('subcategorias/<int:pk>/editar/', views.editar_subcategoria, name='editar_subcategoria'),
    path('subcategorias/<int:pk>/deletar/', views.deletar_subcategoria, name='deletar_subcategoria'),

    # Almoxarifados
    path('almoxarifados/', views.lista_almoxarifados, name='lista_almoxarifados'),
    path('almoxarifados/criar/', views.criar_almoxarifado, name='criar_almoxarifado'),
    path('almoxarifados/<int:pk>/editar/', views.editar_almoxarifado, name='editar_almoxarifado'),
    path('almoxarifados/<int:pk>/deletar/', views.deletar_almoxarifado, name='deletar_almoxarifado'),
    
    # AJAX
    path('ajax/subcategorias-por-categoria/', views.get_subcategorias_por_categoria, name='get_subcategorias_por_categoria'),
]