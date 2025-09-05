# cadastros_base/models.py

from django.db import models
from datetime import timedelta  # Importe timedelta para trabalhar com durações
from django.utils import timezone  # Importe timezone para cálculos de data/hora

# Opções para os dias da semana (usaremos um inteiro para armazenar no BD e exibir o nome)
DIAS_SEMANA_CHOICES = [
    (0, 'Segunda-feira'),
    (1, 'Terça-feira'),
    (2, 'Quarta-feira'),
    (3, 'Quinta-feira'),
    (4, 'Sexta-feira'),
    (5, 'Sábado'),
    (6, 'Domingo'),
]


class UnidadeMedida(models.Model):
    nome = models.CharField(max_length=50, unique=True,
                            verbose_name="Nome da Unidade")
    simbolo = models.CharField(
        max_length=10, unique=True, verbose_name="Símbolo")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Unidade de Medida"
        verbose_name_plural = "Unidades de Medida"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.simbolo})"


class Turno(models.Model):
    # 'nome' foi renomeado para 'descricao' para refletir a imagem
    descricao = models.CharField(
        max_length=100, unique=True, verbose_name="Descrição do Turno")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        ordering = ['descricao']  # Ordena por descrição

    def __str__(self):
        return self.descricao

    # Estes campos não são armazenados diretamente no banco de dados,
    # mas são calculados dinamicamente com base nos 'TurnoDetalheDia' relacionados.

    @property
    def tempo_disponivel_semanal_display(self):
        """Calcula o tempo total disponível na semana para este turno."""
        total_duration = timedelta(0)
        # Itera sobre todos os detalhes diários relacionados a este turno
        for detail in self.turnodetalhedia_set.all():
            # Soma a duração líquida de cada dia
            total_duration += detail.duracao_liquida_calculada

        total_seconds = total_duration.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)

        if hours == 0 and minutes == 0:
            return "0 Hora(s)"
        elif minutes == 0:
            return f"{hours} Hora(s)" if hours == 1 else f"{hours} Horas(s)"
        else:
            return f"{hours}h {minutes}m"

    @property
    def dias_planejados_display(self):
        """Conta quantos dias têm um detalhe de turno definido."""
        # Filtra os detalhes que possuem hora de início definida
        count = self.turnodetalhedia_set.filter(
            hora_inicio__isnull=False).count()
        return f"{count} dia(s)" if count == 1 else f"{count} dias(s)"

    @property
    def horas_por_dia_display(self):
        """Calcula a média de horas por dia com base nos detalhes."""
        total_duration = timedelta(0)
        count = 0
        # Apenas dias com horários
        for detail in self.turnodetalhedia_set.filter(hora_inicio__isnull=False):
            total_duration += detail.duracao_liquida_calculada
            count += 1

        if count > 0:
            avg_seconds = total_duration.total_seconds() / count
            hours = int(avg_seconds // 3600)
            minutes = int((avg_seconds % 3600) // 60)
            if hours == 0 and minutes == 0:
                return "0 Hora(s)"
            elif minutes == 0:
                return f"{hours} Hora(s)" if hours == 1 else f"{hours} Horas(s)"
            else:
                return f"{hours}h {minutes}m"
        return "N/A"  # Se não houver dias planejados


class TurnoDetalheDia(models.Model):
    # Chave estrangeira para o modelo Turno
    turno = models.ForeignKey(
        Turno, on_delete=models.CASCADE, verbose_name="Turno")
    # Dia da semana (0=Segunda, 6=Domingo)
    dia_semana = models.IntegerField(
        choices=DIAS_SEMANA_CHOICES, verbose_name="Dia da Semana")
    hora_inicio = models.TimeField(
        null=True, blank=True, verbose_name="Início")
    hora_fim = models.TimeField(null=True, blank=True, verbose_name="Fim")
    # Intervalo será uma duração (ex: 18 horas de intervalo, como na sua imagem)
    intervalo = models.DurationField(default=timedelta(
        minutes=0), verbose_name="Intervalo (Duração)")

    class Meta:
        verbose_name = "Detalhe do Turno por Dia"
        verbose_name_plural = "Detalhes do Turno por Dia"
        # Garante que um turno só pode ter um detalhe por dia da semana
        unique_together = ('turno', 'dia_semana')
        ordering = ['dia_semana']  # Ordena os detalhes por dia da semana

    def __str__(self):
        return f"{self.turno.descricao} - {self.get_dia_semana_display()}"

    # --- Propriedades calculadas para a duração líquida do dia ---

    @property
    def duracao_liquida_calculada(self):
        """Calcula a duração líquida do turno para o dia, considerando intervalo e virada de dia."""
        if self.hora_inicio and self.hora_fim:
            # Combina a hora com uma data fictícia para criar objetos datetime
            start_dt = timezone.datetime.combine(
                timezone.now().date(), self.hora_inicio)
            end_dt = timezone.datetime.combine(
                timezone.now().date(), self.hora_fim)

            # Se a hora de fim for menor que a hora de início, significa que o turno virou o dia
            if end_dt < start_dt:
                end_dt += timedelta(days=1)  # Adiciona um dia à data de fim

            gross_duration = end_dt - start_dt  # Duração bruta
            # Duração líquida (bruta - intervalo)
            net_duration = gross_duration - self.intervalo

            # Evita duração negativa se o intervalo for maior que a duração bruta
            if net_duration < timedelta(0):
                # Retorna zero ou levanta um erro, dependendo da regra de negócio
                return timedelta(0)

            return net_duration
        # Retorna duração zero se as horas não estiverem definidas
        return timedelta(0)

    @property
    def duracao_liquida_display(self):
        """Formata a duração líquida para exibição (ex: '1 Hora', '8h 30m')."""
        duration = self.duracao_liquida_calculada
        total_seconds = duration.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)

        if hours == 0 and minutes == 0:
            return "0 Horas"
        elif minutes == 0:
            return f"{hours} Hora(s)" if hours == 1 else f"{hours} Horas"
        else:
            return f"{hours}h {minutes}m"
