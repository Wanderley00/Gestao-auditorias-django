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

from django.db.models import Q


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
    # --- NOVOS CAMPOS PARA VERSIONAMENTO ---
    version = models.PositiveIntegerField(default=1, verbose_name="Versão")
    is_latest = models.BooleanField(
        default=True, verbose_name="É a versão mais recente")
    original_checklist = models.ForeignKey(
        'self',
        # Usar SET_NULL para não perder o histórico se o original for deletado
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='versions',
        verbose_name="Checklist Original"
    )
    # --- FIM DOS NOVOS CAMPOS ---
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Checklist"
        verbose_name_plural = "Checklists"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} (V{self.version})"


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
    # <-- ADICIONE ESTA LINHA
    ordem = models.IntegerField(default=0, verbose_name="Ordem")

    class Meta:
        verbose_name = "Opção de Resposta"
        verbose_name_plural = "Opções de Resposta"
        ordering = ['ordem', 'descricao']  # <-- MODIFIQUE ESTA LINHA

    def __str__(self):
        return f"{self.descricao} ({self.get_status_display()})"


class OpcaoPorcentagem(models.Model):
    pergunta = models.ForeignKey(
        Pergunta, on_delete=models.CASCADE, related_name='opcoes_porcentagem')
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    peso = models.PositiveIntegerField(verbose_name="Peso (%)")
    # Para armazenar o código hexadecimal da cor
    cor = models.CharField(max_length=7, default='#FFFFFF', verbose_name="Cor")
    # <-- ADICIONE ESTA LINHA
    ordem = models.IntegerField(default=0, verbose_name="Ordem")

    class Meta:
        verbose_name = "Opção de Porcentagem"
        verbose_name_plural = "Opções de Porcentagem"
        ordering = ['ordem', 'peso']  # <-- MODIFIQUE ESTA LINHA

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
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Criado por",
        related_name='auditorias_criadas',  # 'related_name' para evitar conflito
        editable=False  # Impede que seja editado pelo painel de admin)
    )
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

    @property
    def get_programacao_display(self):
        """ Retorna uma string descrevendo o tipo de agendamento. """
        if self.por_frequencia and self.frequencia:
            # get_frequencia_display() pega o nome legível (ex: 'Semanal')
            return f"Frequência ({self.get_frequencia_display()})"
        elif self.por_intervalo and self.intervalo:
            return f"Intervalo de {self.intervalo} dia(s)"
        else:
            # Se não for por frequência nem intervalo, é uma auditoria de data única
            return "Dia Único"

    def save(self, *args, **kwargs):
        """
        Sobrescrevemos o save apenas para garantir a chamada do método pai.
        Toda a lógica de criação de instâncias foi movida para as views.
        """
        super().save(*args, **kwargs)


class AuditoriaInstancia(models.Model):
    auditoria_agendada = models.ForeignKey(
        Auditoria,
        on_delete=models.CASCADE,
        verbose_name="Auditoria Agendada",
        related_name='instancias'
    )

    # --- NOVO CAMPO PARA VINCULAR A VERSÃO EXATA DO CHECKLIST ---
    checklist_usado = models.ForeignKey(
        Checklist,
        on_delete=models.PROTECT,  # Protege contra a exclusão do checklist se houver auditorias
        null=True, blank=True,
        verbose_name="Checklist Utilizado"
    )
    # --- FIM DO NOVO CAMPO ---

    turno = models.ForeignKey(
        Turno,
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Turno de Execução"
    )

    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Auditor da Execução")

    local_execucao = models.ForeignKey(
        SubSetor,
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Local de Execução (Subsetor)")

    data_execucao = models.DateField(verbose_name="Data de Execução")
    executada = models.BooleanField(default=False, verbose_name="Executada?")

    @property
    def status(self):
        """Calcula o status desta instância específica."""
        if self.executada:
            return "Concluída"

        if self.data_execucao < timezone.now().date():
            return "Atrasada"

        return "Pendente"
    # --- FIM DA ADIÇÃO ---

    @property
    def status_execucao(self):
        """ Retorna o status específico para a tela de execuções, considerando a frequência. """
        today = timezone.now().date()

        if self.executada:
            return "Concluída"

        # Se a data de execução ainda está no futuro, está 'Agendada'
        if self.data_execucao > today:
            return "Agendada"

        # Se a data de execução é hoje, está 'Pendente'
        if self.data_execucao == today:
            return "Pendente"

        # Se a data de execução já passou, verificamos se está em atraso real
        if self.data_execucao < today:
            agendamento = self.auditoria_agendada
            # Padrão de 1 dia para auditorias únicas
            grace_period = timedelta(days=1)

            if agendamento.por_frequencia and agendamento.frequencia:
                if agendamento.frequencia == 'DIARIO':
                    grace_period = timedelta(days=1)
                elif agendamento.frequencia == 'SEMANAL':
                    grace_period = timedelta(weeks=1)
                elif agendamento.frequencia == 'QUINZENAL':
                    grace_period = timedelta(weeks=2)
                elif agendamento.frequencia == 'MENSAL':
                    grace_period = relativedelta(months=1)
                elif agendamento.frequencia == 'ANUAL':
                    grace_period = relativedelta(years=1)

            elif agendamento.por_intervalo and agendamento.intervalo:
                grace_period = timedelta(days=agendamento.intervalo + 1)

            # A data limite é a data programada + o período de carência
            data_limite = self.data_execucao + grace_period

            if today >= data_limite:
                return "Atraso"
            else:
                # Se a data de hoje ainda está dentro do período de carência, continua pendente
                return "Pendente"

        return "Pendente"  # Fallback para o dia de hoje

    def get_data_conclusao(self):
        """Retorna a data e hora da última resposta enviada para esta instância."""
        ultima_resposta = self.respostas.order_by('-data_resposta').first()
        if ultima_resposta:
            return ultima_resposta.data_resposta
        return None

    def get_total_perguntas(self):
        """
        Calcula o número total de perguntas DO CHECKLIST ESPECÍFICO
        usado para esta instância.
        """
        # --- ALTERAÇÃO AQUI ---
        # A lógica antiga olhava para o agendamento pai, que sempre tem a última versão.
        # A nova lógica olha para o checklist exato que foi salvo nesta instância.
        if self.checklist_usado:
            return Pergunta.objects.filter(topico__checklist=self.checklist_usado).count()

        # Se por algum motivo não houver um checklist vinculado, retorna 0 para evitar erros.
        return 0

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

    # --- ADICIONE OS CAMPOS ABAIXO ---
    oportunidade_melhoria = models.BooleanField(
        null=True, blank=True, verbose_name="Oportunidade de Melhoria"
    )
    desvio_solucionado = models.BooleanField(
        null=True, blank=True, verbose_name="Desvio Solucionado na Hora"
    )
    grau_nc = models.CharField(
        max_length=20,
        null=True, blank=True,
        choices=[('NC MAIOR', 'NC Maior'), ('NC MENOR', 'NC Menor')],
        verbose_name="Grau da Não Conformidade"
    )
    data_resposta = models.DateTimeField(
        verbose_name="Data da Resposta", null=True, blank=True)

    class Meta:
        verbose_name = "Resposta"
        verbose_name_plural = "Respostas"
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
