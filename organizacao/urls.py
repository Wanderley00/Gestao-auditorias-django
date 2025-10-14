# organizacao/urls.py

from django.urls import path
from . import views

app_name = 'organizacao'

urlpatterns = [
    # URLs para Empresas
    path('empresas/', views.lista_empresas, name='lista_empresas'),
    path('empresas/criar/', views.criar_empresa, name='criar_empresa'),
    path('empresas/<int:pk>/editar/', views.editar_empresa, name='editar_empresa'),
    path('empresas/<int:pk>/deletar/',
         views.deletar_empresa, name='deletar_empresa'),
    path('empresas/exportar-csv/', views.exportar_empresas_csv,
         name='exportar_empresas_csv'),  # NOVO

    # URLs para Áreas
    path('areas/', views.lista_areas, name='lista_areas'),
    path('areas/criar/', views.criar_area, name='criar_area'),
    path('areas/<int:pk>/editar/', views.editar_area, name='editar_area'),
    path('areas/<int:pk>/deletar/', views.deletar_area, name='deletar_area'),
    path('areas/exportar-csv/', views.exportar_areas_csv,
         name='exportar_areas_csv'),  # NOVO

    # URLs para Setores
    path('setores/', views.lista_setores, name='lista_setores'),
    path('setores/criar/', views.criar_setor, name='criar_setor'),
    path('setores/<int:pk>/editar/', views.editar_setor, name='editar_setor'),
    path('setores/<int:pk>/deletar/', views.deletar_setor, name='deletar_setor'),
    path('setores/exportar-csv/', views.exportar_setores_csv,
         name='exportar_setores_csv'),  # NOVO

    # URLs para Subsetores
    path('subsetores/', views.lista_subsetores, name='lista_subsetores'),
    path('subsetores/criar/', views.criar_subsetor, name='criar_subsetor'),
    path('subsetores/<int:pk>/editar/',
         views.editar_subsetor, name='editar_subsetor'),
    path('subsetores/<int:pk>/deletar/',
         views.deletar_subsetor, name='deletar_subsetor'),
    path('subsetores/exportar-csv/', views.exportar_subsetores_csv,
         name='exportar_subsetores_csv'),  # NOVO
]
