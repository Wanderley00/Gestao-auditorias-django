# fornecedores/urls.py

from django.urls import path
from . import views

app_name = 'fornecedores'

urlpatterns = [
    # URLs para Fornecedores
    path('', views.lista_fornecedores, name='lista_fornecedores'),
    path('criar/', views.criar_fornecedor, name='criar_fornecedor'),
    path('<int:pk>/editar/', views.editar_fornecedor, name='editar_fornecedor'),
    path('<int:pk>/deletar/', views.deletar_fornecedor, name='deletar_fornecedor'),
]
