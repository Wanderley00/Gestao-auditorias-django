# auditorias/admin.py

from django.contrib import admin
from .models import (
    Pilar,
    CategoriaAuditoria,
    Norma,
    RequisitoNorma,
    FerramentaDigital,
    Checklist,
    FerramentaCausaRaiz,
    ModeloAuditoria,
    Auditoria,
    AuditoriaInstancia,
    Topico,
    Pergunta,
    OpcaoResposta,
    OpcaoPorcentagem,
)

@admin.register(Pilar)
class PilarAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao', 'ativo', 'data_cadastro')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao')
    fieldsets = (
        (None, {
            'fields': ('nome', 'descricao', 'ativo')
        }),
    )

@admin.register(CategoriaAuditoria)
class CategoriaAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'pilar', 'descricao', 'ativo', 'data_cadastro')
    list_filter = ('ativo', 'pilar')
    search_fields = ('descricao', 'pilar__nome')
    fieldsets = (
        (None, {
            'fields': ('pilar', 'descricao', 'ativo')
        }),
    )

class RequisitoNormaInline(admin.TabularInline):
    model = RequisitoNorma
    extra = 0
    min_num = 1
    fields = ('codigo', 'requisito', 'descricao', 'ativo')

@admin.register(Norma)
class NormaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'revisao', 'ativo', 'data_cadastro')
    list_filter = ('ativo',)
    search_fields = ('descricao', 'revisao')
    inlines = [RequisitoNormaInline]
    fieldsets = (
        (None, {
            'fields': ('descricao', 'revisao', 'ativo')
        }),
    )

@admin.register(FerramentaDigital)
class FerramentaDigitalAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(FerramentaCausaRaiz)
class FerramentaCausaRaizAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(ModeloAuditoria)
class ModeloAuditoriaAdmin(admin.ModelAdmin):
    list_display = (
        'descricao',
        'checklist',
        'categoria',
        'ferramenta_causa_raiz',
        'ativo',
        'iniciar_por_codigo_qr',
        'data_cadastro'
    )
    list_filter = (
        'ativo',
        'iniciar_por_codigo_qr',
        'checklist',
        'categoria',
        'ferramenta_causa_raiz'
    )
    search_fields = (
        'descricao',
        'checklist__nome',
        'categoria__descricao',
        'ferramenta_causa_raiz__nome'
    )
    fieldsets = (
        (None, {
            'fields': ('descricao', 'checklist', 'categoria', 'ferramenta_causa_raiz', 'ativo', 'iniciar_por_codigo_qr')
        }),
    )

@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'responsavel',
        'nivel_organizacional',
        'ferramenta',
        'data_inicio',
        'data_fim',
        'data_criacao'
    )
    list_filter = (
        'nivel_organizacional',
        'ferramenta',
        'responsavel',
        'data_inicio'
    )
    search_fields = (
        'responsavel__first_name',
        'responsavel__last_name',
        'responsavel__username',
        'local_empresa__nome',
        'local_area__nome',
        'local_setor__nome',
        'local_subsetor__nome'
    )
    filter_horizontal = ('modelos', 'ativos_auditados', 'turnos')
    fieldsets = (
        ("Informações Gerais", {
            'fields': ('ferramenta', 'responsavel', 'categoria_auditoria')
        }),
        ("Localização", {
            'fields': ('nivel_organizacional', 'local_empresa', 'local_area', 'local_setor', 'local_subsetor')
        }),
        ("Seleção de Conteúdo", {
            'fields': ('modelos', 'ativos_auditados')
        }),
        ("Programação", {
            'fields': ('data_inicio', 'data_fim', ('por_frequencia', 'por_intervalo'), 'frequencia', 'intervalo', 'numero_repeticoes', 'pular_finais_semana', 'contem_turnos', 'turnos')
        }),
    )

@admin.register(AuditoriaInstancia)
class AuditoriaInstanciaAdmin(admin.ModelAdmin):
    list_display = ('auditoria_agendada', 'data_execucao', 'executada')
    list_filter = ('executada', 'data_execucao')
    search_fields = ('auditoria_agendada__descricao',)

class OpcaoRespostaInline(admin.TabularInline):
    model = OpcaoResposta
    extra = 0
    fields = ('descricao', 'status')

class OpcaoPorcentagemInline(admin.TabularInline):
    model = OpcaoPorcentagem
    extra = 0
    fields = ('descricao', 'peso', 'cor')

@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ('topico', 'descricao', 'obrigatoria', 'campo_desabilitado')
    list_filter = ('obrigatoria', 'campo_desabilitado')
    search_fields = ('descricao',)
    inlines = [OpcaoRespostaInline, OpcaoPorcentagemInline]

class PerguntaInline(admin.TabularInline):
    model = Pergunta
    extra = 0
    fields = ('descricao', 'obrigatoria', 'campo_desabilitado', 'ordem')

@admin.register(Topico)
class TopicoAdmin(admin.ModelAdmin):
    list_display = ('checklist', 'descricao', 'ordem')
    list_filter = ('checklist',)
    search_fields = ('descricao',)
    inlines = [PerguntaInline]

class TopicoInline(admin.TabularInline):
    model = Topico
    extra = 0
    fields = ('descricao', 'ordem')

@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'ativo',
        'ferramenta',
    )
    list_filter = ('ativo', 'ferramenta')
    search_fields = ('nome',)
    inlines = [TopicoInline]