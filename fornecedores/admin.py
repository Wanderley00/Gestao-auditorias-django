# fornecedores/admin.py

from django.contrib import admin
from .models import Fornecedor


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'npr',
        'usuario_responsavel',  # Exibe o usuário associado
        'ativo',
        'data_cadastro'
    )
    list_filter = ('ativo', 'usuario_responsavel')
    search_fields = ('nome', 'npr', 'usuario_responsavel__username',
                     'usuario_responsavel__first_name', 'usuario_responsavel__last_name')
    fieldsets = (
        (None, {
            'fields': ('nome', 'npr',)
        }),
        ('Associação', {
            'fields': ('usuario_responsavel',)
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )
