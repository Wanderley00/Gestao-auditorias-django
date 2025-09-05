# clientes/admin.py

from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'npr',
        'email',
        'usuario_responsavel',  # Exibe o usuário associado
        'ativo',
        'data_cadastro'
    )
    list_filter = ('ativo', 'usuario_responsavel')
    search_fields = ('nome', 'npr', 'email', 'usuario_responsavel__username',
                     'usuario_responsavel__first_name', 'usuario_responsavel__last_name')
    fieldsets = (
        (None, {
            'fields': ('nome', 'npr', 'email', 'logo_cliente')
        }),
        ('Associação', {
            'fields': ('usuario_responsavel',)
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )
