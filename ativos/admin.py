# ativos/admin.py

from django.contrib import admin
from .models import Categoria, Marca, Modelo, Ativo


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'data_cadastro')
    list_filter = ('ativo',)
    search_fields = ('nome',)


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'data_cadastro')
    list_filter = ('ativo',)
    search_fields = ('nome',)


@admin.register(Modelo)
class ModeloAdmin(admin.ModelAdmin):
    list_display = ('nome', 'marca', 'ativo', 'data_cadastro')
    list_filter = ('ativo', 'marca')
    search_fields = ('nome', 'marca__nome')


@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = (
        'tag',
        'descricao',
        'categoria',
        'marca',
        'modelo',
        'estrutura_organizacional',  # Exibe o subsetor
        'ativo',
        'data_cadastro'
    )
    list_filter = ('ativo', 'categoria', 'marca', 'modelo',
                   'estrutura_organizacional__setor__area__empresa')  # Filtros úteis
    search_fields = (
        'tag',
        'descricao',
        'codigo_fabricante',
        'categoria__nome',
        'marca__nome',
        'modelo__nome',
        'estrutura_organizacional__nome',
        'estrutura_organizacional__setor__nome',
        'estrutura_organizacional__setor__area__nome',
        'estrutura_organizacional__setor__area__empresa__nome'
    )
    # Campos que aparecem no formulário de adicionar/editar
    fieldsets = (
        (None, {
            'fields': ('tag', 'descricao', 'custo', 'codigo_fabricante', 'imagem_ativo')
        }),
        ('Classificação', {
            'fields': ('categoria', 'marca', 'modelo')
        }),
        ('Localização', {
            'fields': ('estrutura_organizacional',)
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )
