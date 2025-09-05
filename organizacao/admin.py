from django.contrib import admin
from .models import Empresa, Area, Setor, SubSetor


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'usuario_responsavel', 'ativo', 'data_cadastro')
    list_filter = ('ativo', 'usuario_responsavel')
    search_fields = ('nome', 'cnpj', 'endereco',
                     'usuario_responsavel__username')
    fieldsets = (
        (None, {
            'fields': ('nome', 'cnpj', 'endereco', 'ativo', 'usuario_responsavel')
        }),
    )


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'empresa', 'usuario_responsavel',
                    'ativo', 'data_cadastro')
    list_filter = ('ativo', 'empresa', 'usuario_responsavel')
    search_fields = ('nome', 'empresa__nome', 'usuario_responsavel__username')
    fieldsets = (
        (None, {
            'fields': ('empresa', 'nome', 'ativo', 'usuario_responsavel')
        }),
    )


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'area', 'usuario_responsavel',
                    'ativo', 'data_cadastro')
    list_filter = ('ativo', 'area__empresa', 'area', 'usuario_responsavel')
    search_fields = ('nome', 'area__nome', 'area__empresa__nome',
                     'usuario_responsavel__username')
    fieldsets = (
        (None, {
            'fields': ('area', 'nome', 'ativo', 'usuario_responsavel')
        }),
    )


@admin.register(SubSetor)
class SubSetorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'setor', 'usuario_responsavel',
                    'ativo', 'data_cadastro')
    list_filter = ('ativo', 'setor__area__empresa',
                   'setor__area', 'setor', 'usuario_responsavel')
    search_fields = ('nome', 'setor__nome', 'setor__area__nome',
                     'setor__area__empresa__nome', 'usuario_responsavel__username')
    fieldsets = (
        (None, {
            'fields': ('setor', 'nome', 'ativo', 'usuario_responsavel')
        }),
    )
