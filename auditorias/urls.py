# auditorias/urls.py

from django.urls import path
from . import views

app_name = 'auditorias'

urlpatterns = [
    path('dashboard/', views.dashboard_auditorias, name='dashboard'),

    path('pilares/', views.lista_pilares, name='lista_pilares'),
    path('pilares/criar/', views.criar_pilar, name='criar_pilar'),
    path('pilares/<int:pk>/editar/', views.editar_pilar, name='editar_pilar'),
    path('pilares/<int:pk>/deletar/', views.deletar_pilar, name='deletar_pilar'),
    path('pilares/exportar-csv/', views.exportar_pilares_csv,
         name='exportar_pilares_csv'),  # NOVO

    path('categorias/', views.lista_categorias_auditoria,
         name='lista_categorias_auditoria'),
    path('categorias/criar/', views.criar_categoria_auditoria,
         name='criar_categoria_auditoria'),
    path('categorias/<int:pk>/editar/', views.editar_categoria_auditoria,
         name='editar_categoria_auditoria'),
    path('categorias/<int:pk>/deletar/', views.deletar_categoria_auditoria,
         name='deletar_categoria_auditoria'),
    path('categorias/exportar-csv/', views.exportar_categorias_auditoria_csv,
         name='exportar_categorias_auditoria_csv'),  # NOVO

    path('normas/', views.lista_normas, name='lista_normas'),
    path('normas/criar/', views.criar_norma, name='criar_norma'),
    path('normas/<int:pk>/editar/', views.editar_norma, name='editar_norma'),
    path('normas/<int:pk>/deletar/', views.deletar_norma, name='deletar_norma'),
    path('normas/exportar-csv/', views.exportar_normas_csv,
         name='exportar_normas_csv'),  # NOVO

    path('ferramentas-digitais/', views.lista_ferramentas_digitais,
         name='lista_ferramentas_digitais'),
    path('ferramentas-digitais/criar/', views.criar_ferramenta_digital,
         name='criar_ferramenta_digital'),
    path('ferramentas-digitais/<int:pk>/editar/',
         views.editar_ferramenta_digital, name='editar_ferramenta_digital'),
    path('ferramentas-digitais/<int:pk>/deletar/',
         views.deletar_ferramenta_digital, name='deletar_ferramenta_digital'),
    path('ferramentas-digitais/exportar-csv/', views.exportar_ferramentas_digitais_csv,
         name='exportar_ferramentas_digitais_csv'),  # NOVO

    path('checklists/', views.lista_checklists, name='lista_checklists'),
    path('checklists/criar/', views.criar_checklist, name='criar_checklist'),
    path('checklists/<int:pk>/editar/',
         views.editar_checklist, name='editar_checklist'),
    path('checklists/<int:pk>/deletar/',
         views.deletar_checklist, name='deletar_checklist'),
    path('checklists/exportar-csv/', views.exportar_checklists_csv,
         name='exportar_checklists_csv'),  # NOVO

    path('modelos-auditoria/', views.lista_modelos_auditoria,
         name='lista_modelos_auditoria'),
    path('modelos-auditoria/criar/', views.criar_modelo_auditoria,
         name='criar_modelo_auditoria'),
    path('modelos-auditoria/<int:pk>/editar/',
         views.editar_modelo_auditoria, name='editar_modelo_auditoria'),
    path('modelos-auditoria/exportar-csv/', views.exportar_modelos_auditoria_csv,
         name='exportar_modelos_auditoria_csv'),  # NOVO

    path('agendamentos/<int:pk>/redirecionar/',
         views.redirecionar_agendamento, name='redirecionar_agendamento'),
    path('execucoes/<int:pk>/redirecionar/',
         views.redirecionar_execucao, name='redirecionar_execucao'),

    path('modelos-auditoria/<int:pk>/deletar/',
         views.deletar_modelo_auditoria, name='deletar_modelo_auditoria'),

    path('auditorias/', views.lista_auditorias, name='lista_auditorias'),
    path('auditorias/criar/', views.criar_auditoria, name='criar_auditoria'),
    path('auditorias/<int:pk>/editar/',
         views.editar_auditoria, name='editar_auditoria'),
    path('auditorias/<int:pk>/deletar/',
         views.deletar_auditoria, name='deletar_auditoria'),

    path('ajax/areas-por-empresa/', views.get_areas_por_empresa,
         name='get_areas_por_empresa'),
    path('ajax/setores-por-area/', views.get_setores_por_area,
         name='get_setores_por_area'),
    path('ajax/subsetores-por-setor/', views.get_subsetores_por_setor,
         name='get_subsetores_por_setor'),
    path('ajax/ativos-por-local/', views.get_ativos_por_local,
         name='get_ativos_por_local'),

    path('ajax/preview-dates/', views.preview_audit_dates,
         name='preview_audit_dates'),

    path('execucoes/', views.lista_execucoes, name='lista_execucoes'),

    path('historico/', views.historico_concluidas, name='historico_concluidas'),

    path('execucoes/<int:pk>/deletar/',
         views.deletar_execucao, name='deletar_execucao'),

    path('checklists/<int:pk>/historico/',
         views.historico_versoes_checklist, name='historico_versoes_checklist'),

    path('checklists/<int:pk>/comparar/', views.comparar_versoes_checklist,
         name='comparar_versoes_checklist'),

    path('historico/<int:pk>/detalhes/',
         views.detalhes_auditoria, name='detalhes_auditoria'),


    path('historico/<int:pk>/visualizar/',
         views.detalhes_historico_auditoria, name='detalhes_historico_auditoria'),

]
