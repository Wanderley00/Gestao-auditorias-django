# auditorias/models.py

from django.db import models
from django.contrib.auth.models import User
from organizacao.models import Empresa, Area, Setor, SubSetor
from ativos.models import Ativo
from cadastros_base.models import Turno
from django.conf import settings

from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class Pilar(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name="Nome do Pilar")
    descricao = models.TextField(
        null=True, blank=True, verbose_name="Descrição")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Pilar"
        verbose_name_plural = "Pilares"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class CategoriaAuditoria(models.Model):
    pilar = models.ForeignKey(
        Pilar,
        on_delete=models.CASCADE,
        verbose_name="Pilar",
        related_name='categorias_auditoria'
    )
    descricao = models.CharField(
        max_length=255, verbose_name="Descrição da Categoria")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Categoria de Auditoria"
        verbose_name_plural = "Categorias de Auditorias"
        unique_together = ('pilar', 'descricao')
        ordering = ['pilar__nome', 'descricao']

    def __str__(self):
        return f"{self.descricao} ({self.pilar.nome})"


class Norma(models.Model):
    descricao = models.CharField(
        max_length=255, unique=True, verbose_name="Descrição da Norma")
    revisao = models.CharField(max_length=100, verbose_name="Revisão")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Norma"
        verbose_name_plural = "Normas"
        unique_together = ('descricao', 'revisao')
        ordering = ['descricao', 'revisao']

    def __str__(self):
        return f"{self.descricao} (Rev. {self.revisao})"


class RequisitoNorma(models.Model):
    norma = models.ForeignKey(
        Norma,
        on_delete=models.CASCADE,
        verbose_name="Norma",
        related_name='requisitos'
    )
    codigo = models.CharField(max_length=50, verbose_name="Código")
    requisito = models.CharField(max_length=255, verbose_name="Requisito")
    descricao = models.TextField(
        null=True, blank=True, verbose_name="Descrição")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Requisito de Norma"
        verbose_name_plural = "Requisitos de Normas"
        unique_together = ('norma', 'codigo')
        ordering = ['norma__descricao', 'codigo']

    def __str__(self):
        return f"{self.codigo} - {self.norma.descricao}"


class FerramentaDigital(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name="Nome da Ferramenta")

    class Meta:
        verbose_name = "Ferramenta Digital"
        verbose_name_plural = "Ferramentas Digitais"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Checklist(models.Model):
    nome = models.CharField(max_length=255, verbose_name="Nome do Checklist")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    ferramenta = models.ForeignKey(
        FerramentaDigital,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Ferramenta Digital",
        related_name='checklists'
    )
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Checklist"
        verbose_name_plural = "Checklists"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Topico(models.Model):
    checklist = models.ForeignKey(
        Checklist,
        on_delete=models.CASCADE,
        verbose_name="Checklist",
        related_name='topicos'
    )
    descricao = models.CharField(
        max_length=255, verbose_name="Descrição do Tópico")
    ordem = models.IntegerField(default=0, verbose_name="Ordem")

    class Meta:
        verbose_name = "Tópico"
        verbose_name_plural = "Tópicos"
        unique_together = ('checklist', 'descricao')
        ordering = ['ordem', 'descricao']

    def __str__(self):
        return self.descricao


class Pergunta(models.Model):
    topico = models.ForeignKey(
        Topico,
        on_delete=models.CASCADE,
        verbose_name="Tópico",
        related_name='perguntas'
    )
    descricao = models.TextField(verbose_name="Descrição da Pergunta")

    # Novos campos para tipos de resposta
    resposta_livre = models.BooleanField(
        default=False, verbose_name="Permitir Resposta Livre")
    foto = models.BooleanField(default=False, verbose_name="Permitir Foto")
    criar_opcao = models.BooleanField(
        default=True, verbose_name="Permitir Criar uma Opção")
    porcentagem = models.BooleanField(
        default=False, verbose_name="Permitir Porcentagem")

    # Campo para definir se a resposta é obrigatória
    obrigatoria = models.BooleanField(
        default=False, verbose_name="Resposta Obrigatória")

    campo_obrigatorio = models.BooleanField(
        default=False, verbose_name="Campo Obrigatório")
    campo_desabilitado = models.BooleanField(
        default=False, verbose_name="Campo Desabilitado")
    ordem = models.IntegerField(default=0, verbose_name="Ordem")

    class Meta:
        verbose_name = "Pergunta"
        verbose_name_plural = "Perguntas"
        unique_together = ('topico', 'descricao')
        ordering = ['ordem', 'descricao']

    def __str__(self):
        return self.descricao[:50] + '...' if len(self.descricao) > 50 else self.descricao


class OpcaoResposta(models.Model):
    pergunta = models.ForeignKey(
        Pergunta, on_delete=models.CASCADE, related_name='opcoes_resposta')
    descricao = models.CharField(
        max_length=255, verbose_name="Descrição da Opção")
    status = models.CharField(
        max_length=20,
        choices=[
            ('CONFORME', 'Conforme'),
            ('NAO_CONFORME', 'Não Conforme'),
            ('DESVIO_SOLUCIONADO', 'Desvio Solucionado'),
            ('NA', 'N/A'),
        ],
        verbose_name="Status Vinculado"
    )

    class Meta:
        verbose_name = "Opção de Resposta"
        verbose_name_plural = "Opções de Resposta"
        ordering = ['descricao']

    def __str__(self):
        return f"{self.descricao} ({self.get_status_display()})"


class OpcaoPorcentagem(models.Model):
    pergunta = models.ForeignKey(
        Pergunta, on_delete=models.CASCADE, related_name='opcoes_porcentagem')
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    peso = models.PositiveIntegerField(verbose_name="Peso (%)")
    # Para armazenar o código hexadecimal da cor
    cor = models.CharField(max_length=7, default='#FFFFFF', verbose_name="Cor")

    class Meta:
        verbose_name = "Opção de Porcentagem"
        verbose_name_plural = "Opções de Porcentagem"
        ordering = ['peso']

    def __str__(self):
        return f"{self.descricao} - {self.peso}%"


class FerramentaCausaRaiz(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name="Nome da Ferramenta")

    class Meta:
        verbose_name = "Ferramenta de Causa Raiz"
        verbose_name_plural = "Ferramentas de Causa Raiz"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class ModeloAuditoria(models.Model):
    descricao = models.CharField(
        max_length=255, verbose_name="Descrição do Modelo")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    iniciar_por_codigo_qr = models.BooleanField(
        default=False, verbose_name="Iniciar por Código QR")
    checklist = models.ForeignKey(
        Checklist,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Checklist",
        related_name='modelos_auditoria'
    )
    categoria = models.ForeignKey(
        CategoriaAuditoria,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Categoria",
        related_name='modelos_auditoria'
    )
    ferramenta_causa_raiz = models.ForeignKey(
        FerramentaCausaRaiz,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Ferramenta para Causa Raiz",
        related_name='modelos_auditoria'
    )
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Modelo de Auditoria"
        verbose_name_plural = "Modelos de Auditoria"
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


NIVEIS_ORGANIZACIONAIS = [
    ('EMPRESA', 'Empresa'),
    ('AREA', 'Área'),
    ('SETOR', 'Setor'),
    ('SUBSETOR', 'Subsetor'),
]

CATEGORIAS_AUDITORIA = [
    ('APP', 'App'),
    ('WEB', 'Web'),
]

FREQUENCIAS_AGENDAMENTO = [
    ('DIARIO', 'Diário'),
    ('SEMANAL', 'Semanal'),
    ('QUINZENAL', 'Quinzenal'),
    ('MENSAL', 'Mensal'),
    ('ANUAL', 'Anual'),
]


class Auditoria(models.Model):
    ferramenta = models.ForeignKey(
        FerramentaDigital,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Ferramenta Digital"
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Responsável"
    )
    nivel_organizacional = models.CharField(
        max_length=50,
        choices=[
            ('EMPRESA', 'Empresa'),
            ('AREA', 'Área'),
            ('SETOR', 'Setor'),
            ('SUBSETOR', 'Subsetor'),
        ],
        verbose_name="Nível"
    )
    local_empresa = models.ForeignKey(
        'organizacao.Empresa',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Local (Empresa)"
    )
    local_area = models.ForeignKey(
        'organizacao.Area',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Local (Área)"
    )
    local_setor = models.ForeignKey(
        'organizacao.Setor',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Local (Setor)"
    )
    local_subsetor = models.ForeignKey(
        'organizacao.SubSetor',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Local (Subsetor)"
    )
    modelos = models.ManyToManyField(
        ModeloAuditoria, verbose_name="Modelos de Auditoria")
    ativos_auditados = models.ManyToManyField(
        Ativo, verbose_name="Ativos Auditados", related_name='auditorias_agendadas')
    categoria_auditoria = models.CharField(
        max_length=10,
        choices=CATEGORIAS_AUDITORIA,
        verbose_name="Categoria"
    )
    turnos = models.ManyToManyField(
        Turno,
        blank=True,
        verbose_name="Turnos"
    )
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(
        null=True, blank=True, verbose_name="Data de Fim")
    por_frequencia = models.BooleanField(
        default=False, verbose_name="Por Frequência")
    por_intervalo = models.BooleanField(
        default=False, verbose_name="Por Intervalo")
    frequencia = models.CharField(
        max_length=10,
        choices=FREQUENCIAS_AGENDAMENTO,
        null=True, blank=True,
        verbose_name="Frequência"
    )
    intervalo = models.IntegerField(
        null=True, blank=True, verbose_name="Intervalo")
    numero_repeticoes = models.IntegerField(
        null=True, blank=True, verbose_name="Número de Repetições")
    pular_finais_semana = models.BooleanField(
        default=False, verbose_name="Pular Finais de Semana")
    contem_turnos = models.BooleanField(
        default=False, verbose_name="Contém Turnos")
    data_criacao = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Auditoria Agendada"
        verbose_name_plural = "Auditorias Agendadas"
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Auditoria agendada para {self.get_nivel_organizacional_display()} - {self.data_inicio}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if not is_new:
            self.instancias.filter(
                executada=False,
                data_execucao__gte=timezone.now().date()
            ).delete()

        # Lógica de geração de instâncias (VERSÃO CORRIGIDA)
        if self.data_inicio:
            dates_to_create = []
            current_date = self.data_inicio
            repetitions = self.numero_repeticoes if self.numero_repeticoes and self.numero_repeticoes > 0 else 1

            # CASO 1: SEM DATA FINAL (AUDITORIA ÚNICA)
            if not self.data_fim:
                if not (self.pular_finais_semana and current_date.weekday() >= 5):
                    for _ in range(repetitions):
                        dates_to_create.append(current_date)

            # CASO 2: COM DATA FINAL
            else:
                loop_limit = 365 * 5
                loops = 0
                while current_date <= self.data_fim and loops < loop_limit:
                    loops += 1

                    if not (self.pular_finais_semana and current_date.weekday() >= 5):
                        for _ in range(repetitions):
                            dates_to_create.append(current_date)

                    # Calcula a próxima data
                    if self.por_intervalo:
                        # LÓGICA DE INTERVALO CORRIGIDA
                        interval = self.intervalo if self.intervalo else 0
                        current_date += timedelta(days=interval + 1)
                    elif self.por_frequencia:
                        if self.frequencia == 'DIARIO':
                            current_date += timedelta(days=1)
                        elif self.frequencia == 'SEMANAL':
                            current_date += timedelta(weeks=1)
                        elif self.frequencia == 'QUINZENAL':
                            current_date += timedelta(weeks=2)
                        elif self.frequencia == 'MENSAL':
                            current_date += relativedelta(months=1)
                        elif self.frequencia == 'ANUAL':
                            current_date += relativedelta(years=1)
                        else:  # Fallback para diário se frequência for inválida
                            current_date += timedelta(days=1)
                    else:  # Intervalo simples de datas
                        current_date += timedelta(days=1)

            # Cria as instâncias no banco de uma forma otimizada
            for dt in dates_to_create:
                AuditoriaInstancia.objects.get_or_create(
                    auditoria_agendada=self,
                    data_execucao=dt
                )


class AuditoriaInstancia(models.Model):
    auditoria_agendada = models.ForeignKey(
        Auditoria,
        on_delete=models.CASCADE,
        verbose_name="Auditoria Agendada",
        related_name='instancias'
    )
    data_execucao = models.DateField(verbose_name="Data de Execução")
    executada = models.BooleanField(default=False, verbose_name="Executada?")

    def get_total_perguntas(self):
        """Calcula o número total de perguntas de todos os checklists associados à auditoria pai."""
        total_perguntas = 0
        # Itera sobre todos os modelos de auditoria associados à auditoria agendada
        for modelo in self.auditoria_agendada.modelos.all():
            if modelo.checklist:
                # Conta o número de perguntas em cada checklist
                total_perguntas += Pergunta.objects.filter(
                    topico__checklist=modelo.checklist).count()
        return total_perguntas

    def get_percentual_conclusao(self):
        """Calcula e formata o percentual de respostas concluídas."""
        total_perguntas = self.get_total_perguntas()
        respostas_dadas = self.respostas.count()

        if total_perguntas == 0:
            return 0.0  # Evita divisão por zero se não houver perguntas

        percentual = (respostas_dadas / total_perguntas) * 100
        return round(percentual, 2)

    # --- FIM DA ADIÇÃO ---

    class Meta:
        verbose_name = "Instância de Auditoria"
        verbose_name_plural = "Instâncias de Auditoria"
        ordering = ['data_execucao']

    def __str__(self):
        return f"Execução em {self.data_execucao} de {self.auditoria_agendada}"


class Resposta(models.Model):

    auditoria_instancia = models.ForeignKey(
        AuditoriaInstancia,
        on_delete=models.CASCADE,
        related_name='respostas',
        verbose_name="Instância da Auditoria"
    )
    pergunta = models.ForeignKey(
        Pergunta,
        on_delete=models.CASCADE,
        related_name='respostas',
        verbose_name="Pergunta"
    )
    # Campos para cada tipo de resposta possível (a maioria será nula)
    opcao_resposta = models.ForeignKey(
        OpcaoResposta,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Opção de Resposta Selecionada"
    )
    opcao_porcentagem = models.ForeignKey(
        OpcaoPorcentagem,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Opção de Porcentagem Selecionada"
    )
    resposta_livre_texto = models.TextField(
        null=True, blank=True,
        verbose_name="Texto da Resposta Livre"
    )
    data_resposta = models.DateTimeField(
        auto_now_add=True, verbose_name="Data da Resposta")

    class Meta:
        verbose_name = "Resposta"
        verbose_name_plural = "Respostas"
        # Garante que só haja uma resposta por pergunta em cada auditoria
        unique_together = ('auditoria_instancia', 'pergunta')

    def __str__(self):
        return f"Resposta para '{self.pergunta.descricao[:30]}...' na auditoria {self.auditoria_instancia.id}"


class AnexoResposta(models.Model):
    """
    Armazena os arquivos (fotos) anexados a uma resposta.
    """
    resposta = models.ForeignKey(
        Resposta,
        on_delete=models.CASCADE,
        related_name='anexos',
        verbose_name="Resposta"
    )
    arquivo = models.FileField(
        upload_to='anexos_respostas/', verbose_name="Arquivo")
    data_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Anexo da Resposta"
        verbose_name_plural = "Anexos das Respostas"

    def __str__(self):
        return f"Anexo para a resposta {self.resposta.id}"
