# auditorias/urls.py

from django.urls import path
from . import views

app_name = 'auditorias'  # Este é o namespace!

urlpatterns = [
    path('lista/', views.lista_auditorias, name='lista_auditorias'),
]
