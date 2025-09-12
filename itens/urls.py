# itens/urls.py (novo arquivo)

from django.urls import path
from . import views

app_name = 'itens'

urlpatterns = [
    # Rota para a lista de itens (Ex: /itens/)
    path('', views.lista_itens, name='lista_itens'),
    
    # Rota para o formulário de criação (Ex: /itens/criar/)
    path('criar/', views.criar_item, name='criar_item'),
    
    # Rota para o formulário de edição (Ex: /itens/1/editar/)
    path('<int:pk>/editar/', views.editar_item, name='editar_item'),
    
    # Rota para a ação de deletar (Ex: /itens/1/deletar/)
    path('<int:pk>/deletar/', views.deletar_item, name='deletar_item'),
]