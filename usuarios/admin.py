# usuarios/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario

# Crie uma classe inline para gerenciar o ManyToMany se for o caso


class FornecedorInline(admin.TabularInline):
    model = Usuario.fornecedores.through  # Usar o modelo intermediário para o M2M
    extra = 1


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    # Adicione os campos personalizados aos fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações Adicionais', {'fields': ('registro',)}),
    )

    # Adicione a relação a Fornecedores no `filter_horizontal`
    filter_horizontal = BaseUserAdmin.filter_horizontal + ('fornecedores',)

    # Ajuste o list_display para incluir o novo campo
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'registro',  # Adicione o campo de registro
        'is_staff',
    )

    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'registro'
    )
