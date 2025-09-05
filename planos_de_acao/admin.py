# planos_de_acao/admin.py

from django.contrib import admin
from .models import (
    ResponsavelLocal,
    NaoConformidade,
    Forum,
    MensagemForum
)


@admin.register(ResponsavelLocal)
class ResponsavelLocalAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'local_empresa', 'local_area',
                    'local_setor', 'local_subsetor')
    search_fields = ('usuario__username',
                     'local_empresa__nome', 'local_area__nome')
    fieldsets = (
        (None, {
            'fields': ('usuario', 'local_empresa', 'local_area', 'local_setor', 'local_subsetor')
        }),
    )


@admin.register(NaoConformidade)
class NaoConformidadeAdmin(admin.ModelAdmin):
    list_display = (
        'id_nao_conformidade',
        'id_formulario',
        'titulo',
        'responsavel_acao',
        'data_abertura',
        'data_encerramento',
        'criticidade',
        'local_setor'  # Exibe o setor como exemplo de local
    )
    list_filter = ('criticidade', 'data_abertura', 'responsavel_acao')
    search_fields = ('id_nao_conformidade', 'titulo__descricao')
    filter_horizontal = ('ferramentas_auxiliares',)
    readonly_fields = ('data_abertura', 'data_encerramento',
                       'id_nao_conformidade')
    fieldsets = (
        ("Identificação", {
            'fields': ('id_nao_conformidade', 'id_formulario', 'titulo', 'descricao_desvio')
        }),
        ("Responsabilidade e Ação", {
            'fields': ('responsavel_acao', 'acao_corretiva', 'prazo_conclusao', 'criticidade')
        }),
        ("Detalhes da Auditoria", {
            'fields': ('ferramenta', 'categoria', 'local_empresa', 'local_area', 'local_setor', 'local_subsetor')
        }),
        ("Análise e Suporte", {
            'fields': ('analise', 'ferramentas_auxiliares', 'forum')
        }),
        ("Datas", {
            'fields': ('data_abertura', 'data_encerramento')
        })
    )

# Registro dos modelos de fórum (opcional, mas recomendado)


@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_criacao')


@admin.register(MensagemForum)
class MensagemForumAdmin(admin.ModelAdmin):
    list_display = ('autor', 'forum', 'data_envio')
    list_filter = ('forum', 'autor')
