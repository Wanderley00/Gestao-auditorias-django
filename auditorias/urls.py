# auditorias/urls.py

from django.urls import path
from . import views

app_name = 'auditorias'

urlpatterns = [
    # Dashboard principal (agora em /dashboard/)
    path('dashboard/', views.dashboard_auditorias, name='dashboard'),
    
    # URLs para Pilares
    path('pilares/', views.lista_pilares, name='lista_pilares'),
    path('pilares/criar/', views.criar_pilar, name='criar_pilar'),
    path('pilares/<int:pk>/editar/', views.editar_pilar, name='editar_pilar'),
    path('pilares/<int:pk>/deletar/', views.deletar_pilar, name='deletar_pilar'),
    
    # URLs para Categorias de Auditoria
    path('categorias/', views.lista_categorias_auditoria, name='lista_categorias_auditoria'),
    path('categorias/criar/', views.criar_categoria_auditoria, name='criar_categoria_auditoria'),
    path('categorias/<int:pk>/editar/', views.editar_categoria_auditoria, name='editar_categoria_auditoria'),
    path('categorias/<int:pk>/deletar/', views.deletar_categoria_auditoria, name='deletar_categoria_auditoria'),
    
    
    # URLs para Normas
    path('normas/', views.lista_normas, name='lista_normas'),
    path('normas/criar/', views.criar_norma, name='criar_norma'),
    path('normas/<int:pk>/editar/', views.editar_norma, name='editar_norma'),
    path('normas/<int:pk>/deletar/', views.deletar_norma, name='deletar_norma'),
    
    # URLs para Ferramentas Digitais
    path('ferramentas-digitais/', views.lista_ferramentas_digitais, name='lista_ferramentas_digitais'),
    path('ferramentas-digitais/criar/', views.criar_ferramenta_digital, name='criar_ferramenta_digital'),
    path('ferramentas-digitais/<int:pk>/editar/', views.editar_ferramenta_digital, name='editar_ferramenta_digital'),
    path('ferramentas-digitais/<int:pk>/deletar/', views.deletar_ferramenta_digital, name='deletar_ferramenta_digital'),
    
    # URLs para Tipos de Questão
    path('tipos-questao/', views.lista_tipos_questao, name='lista_tipos_questao'),
    path('tipos-questao/criar/', views.criar_tipo_questao, name='criar_tipo_questao'),
    path('tipos-questao/<int:pk>/editar/', views.editar_tipo_questao, name='editar_tipo_questao'),
    path('tipos-questao/<int:pk>/deletar/', views.deletar_tipo_questao, name='deletar_tipo_questao'),
    
    # URLs para Modelos de Avaliação
    path('modelos-avaliacao/', views.lista_modelos_avaliacao, name='lista_modelos_avaliacao'),
    path('modelos-avaliacao/criar/', views.criar_modelo_avaliacao, name='criar_modelo_avaliacao'),
    path('modelos-avaliacao/<int:pk>/editar/', views.editar_modelo_avaliacao, name='editar_modelo_avaliacao'),
    path('modelos-avaliacao/<int:pk>/deletar/', views.deletar_modelo_avaliacao, name='deletar_modelo_avaliacao'),
    
    # URLs para Checklists
    path('checklists/', views.lista_checklists, name='lista_checklists'),
    path('checklists/criar/', views.criar_checklist, name='criar_checklist'),
    path('checklists/<int:pk>/editar/', views.editar_checklist, name='editar_checklist'),
    path('checklists/<int:pk>/deletar/', views.deletar_checklist, name='deletar_checklist'),
    
    # URLs para Modelos de Auditoria
    path('modelos-auditoria/', views.lista_modelos_auditoria, name='lista_modelos_auditoria'),
    path('modelos-auditoria/criar/', views.criar_modelo_auditoria, name='criar_modelo_auditoria'),
    path('modelos-auditoria/<int:pk>/editar/', views.editar_modelo_auditoria, name='editar_modelo_auditoria'),
    path('modelos-auditoria/<int:pk>/deletar/', views.deletar_modelo_auditoria, name='deletar_modelo_auditoria'),
    
    # URLs para Auditorias Agendadas
    path('auditorias/', views.lista_auditorias, name='lista_auditorias'),
    path('auditorias/criar/', views.criar_auditoria, name='criar_auditoria'),
    path('auditorias/<int:pk>/editar/', views.editar_auditoria, name='editar_auditoria'),
    path('auditorias/<int:pk>/deletar/', views.deletar_auditoria, name='deletar_auditoria'),
    
    # URLs AJAX para filtros dinâmicos
    path('ajax/areas-por-empresa/', views.get_areas_por_empresa, name='get_areas_por_empresa'),
    path('ajax/setores-por-area/', views.get_setores_por_area, name='get_setores_por_area'),
    path('ajax/subsetores-por-setor/', views.get_subsetores_por_setor, name='get_subsetores_por_setor'),
    path('ajax/ativos-por-local/', views.get_ativos_por_local, name='get_ativos_por_local'),
]

