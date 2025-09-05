# itens/admin.py

from django.contrib import admin
from .models import CategoriaItem, SubcategoriaItem, Almoxarifado, Item


@admin.register(CategoriaItem)
class CategoriaItemAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'ativo', 'data_cadastro')
    list_filter = ('ativo',)
    search_fields = ('descricao',)


@admin.register(SubcategoriaItem)
class SubcategoriaItemAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'categoria', 'ativo', 'data_cadastro')
    list_filter = ('ativo', 'categoria')
    search_fields = ('descricao', 'categoria__descricao')


@admin.register(Almoxarifado)
class AlmoxarifadoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'data_cadastro')
    list_filter = ('ativo',)
    search_fields = ('nome', 'endereco')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_interno',
        'descricao',
        'unidade_medida',
        'categoria_principal',
        'subcategoria_principal',
        'almoxarifado',
        'ativo',
        'data_cadastro'
    )
    list_filter = (
        'ativo',
        'unidade_medida',
        'categoria_principal',
        'subcategoria_principal',
        'almoxarifado'
    )
    search_fields = (
        'codigo_interno',
        'codigo_alternativo',
        'descricao',
        'unidade_medida__simbolo',  # Permite buscar pela unidade de medida
        'categoria_principal__descricao',
        'subcategoria_principal__descricao',
        'almoxarifado__nome'
    )
    fieldsets = (
        (None, {
            'fields': (
                'codigo_interno', 'codigo_alternativo', 'descricao',
                'imagem_item'
            )
        }),
        ('Dados Técnicos e Financeiros', {
            'fields': ('unidade_medida', 'peso', 'valor')
        }),
        ('Localização e Classificação', {
            'fields': ('almoxarifado', 'categoria_principal', 'subcategoria_principal')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )
