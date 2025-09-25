# clientes/urls.py

from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    # URLs para Clientes
    path('', views.lista_clientes, name='lista_clientes'),
    path('criar/', views.criar_cliente, name='criar_cliente'),
    path('<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
    path('<int:pk>/deletar/', views.deletar_cliente, name='deletar_cliente'),
]
