# auditorias/admin.py

from django.contrib import admin
from .models import (
    Pilar,
    CategoriaAuditoria,
    Norma,
    RequisitoNorma,
    FerramentaDigital,
    TipoQuestao,
    ModeloAvaliacao,
    Checklist,
    FerramentaCausaRaiz,
    ModeloAuditoria,
    Auditoria,
    AuditoriaInstancia,
    Topico,
    Pergunta,
    OpcaoPergunta,

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

# Inline para permitir adicionar/editar requisitos dentro do formulário de Norma


class RequisitoNormaInline(admin.TabularInline):
    model = RequisitoNorma
    extra = 0  # Não mostra formulários vazios extras por padrão
    min_num = 1  # Garante que pelo menos um requisito seja criado
    fields = ('codigo', 'requisito', 'descricao', 'ativo')


@admin.register(Norma)
class NormaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'revisao', 'ativo', 'data_cadastro')
    list_filter = ('ativo',)
    search_fields = ('descricao', 'revisao')
    # Adiciona o inline para gerenciar os requisitos
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


@admin.register(TipoQuestao)
class TipoQuestaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome', 'descricao')


@admin.register(ModeloAvaliacao)
class ModeloAvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)
    # Melhor para ManyToMany no admin
    filter_horizontal = ('tipos_questao_suportados',)


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
        # O nome do campo não muda, apenas sua referência no banco de dados
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
        'ferramenta_causa_raiz__nome'  # Agora é possível pesquisar pelo nome da ferramenta
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
    # Para as relações ManyToMany, 'filter_horizontal' é mais amigável
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


class OpcaoPerguntaInline(admin.TabularInline):
    model = OpcaoPergunta
    extra = 0
    fields = ('descricao', 'tipo_status', 'instrucoes_usuario')

# Admin para as Perguntas (agora pode referenciar OpcaoPerguntaInline)


@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ('topico', 'descricao', 'tipo_questao',
                    'campo_obrigatorio', 'campo_desabilitado')
    list_filter = ('tipo_questao', 'campo_obrigatorio', 'campo_desabilitado')
    search_fields = ('descricao',)
    inlines = [OpcaoPerguntaInline]


# Inline para as Perguntas do Tópico (colocado ANTES de TopicoAdmin)
class PerguntaInline(admin.TabularInline):
    model = Pergunta
    extra = 0
    fields = ('descricao', 'tipo_questao', 'campo_obrigatorio',
              'campo_desabilitado', 'ordem')


# Admin para os Tópicos (agora pode referenciar PerguntaInline)
@admin.register(Topico)
class TopicoAdmin(admin.ModelAdmin):
    list_display = ('checklist', 'descricao', 'ordem')
    list_filter = ('checklist',)
    search_fields = ('descricao',)
    inlines = [PerguntaInline]


# Inline para os Tópicos do Checklist
class TopicoInline(admin.TabularInline):
    model = Topico
    extra = 0
    fields = ('descricao', 'ordem')


# Admin para o Checklist
@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'ativo',
        'ferramenta',
        'modelo_avaliacao',
    )
    list_filter = ('ativo', 'ferramenta', 'modelo_avaliacao')
    search_fields = ('nome',)
    inlines = [TopicoInline]
