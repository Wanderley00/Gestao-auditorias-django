# cadastros_base/admin.py

from django.contrib import admin
from .models import UnidadeMedida, Turno, TurnoDetalheDia, DIAS_SEMANA_CHOICES
# Nao precisa importar timedelta aqui, pois ja esta no models.py

# Inline para permitir adicionar/editar detalhes diários de um turno na mesma página do Turno


class TurnoDetalheDiaInline(admin.TabularInline):
    model = TurnoDetalheDia
    extra = 0  # Não mostra formulários vazios extras por padrão
    # Permite ter 0 detalhes (se desejar um turno sem dias definidos)
    min_num = 0
    # Máximo de 7 entradas, uma para cada dia da semana
    max_num = len(DIAS_SEMANA_CHOICES)
    # Campos que serão exibidos no inline
    fields = ('dia_semana', 'hora_inicio', 'hora_fim',
              'intervalo', 'duracao_liquida_display')
    # Campos que serão apenas de leitura (não editáveis)
    readonly_fields = ('duracao_liquida_display',)

    # Opcional: Para ordenar a lista de dias na interface do admin
    # Isso pode ser feito no Meta do modelo TurnoDetalheDia (já feito com ordering = ['dia_semana'])


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    # Campos a serem exibidos na lista de Turnos
    list_display = (
        'descricao',
        'ativo',
        'tempo_disponivel_semanal_display',  # Propriedade calculada
        'dias_planejados_display',        # Propriedade calculada
        'horas_por_dia_display',         # Propriedade calculada
    )
    list_filter = ('ativo',)
    search_fields = ('descricao',)
    # Adiciona o inline para gerenciar os detalhes diários
    inlines = [TurnoDetalheDiaInline]

    # Campos que serão exibidos no formulário de edição/criação do Turno
    fields = ('descricao', 'ativo')


@admin.register(UnidadeMedida)
class UnidadeMedidaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'simbolo', 'ativo', 'data_cadastro')
    list_filter = ('ativo',)
    search_fields = ('nome', 'simbolo')
