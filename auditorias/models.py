# auditorias/models.py

from django.db import models

from django.contrib.auth.models import User
# Importe os modelos de organização
from organizacao.models import Empresa, Area, Setor, SubSetor
from ativos.models import Ativo  # Importe o modelo de Ativo
from cadastros_base.models import Turno
from django.conf import settings

# O modelo Pilar já deve estar definido acima deste


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

# Novo modelo: Categoria de Auditoria


class CategoriaAuditoria(models.Model):
    pilar = models.ForeignKey(
        Pilar,
        # Se o pilar for excluído, as categorias associadas também serão
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
        # Garante que uma categoria é única dentro de um pilar
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

# Novo modelo: Requisito de Norma


class RequisitoNorma(models.Model):
    norma = models.ForeignKey(
        Norma,
        # Se a norma for excluída, os requisitos associados também serão
        on_delete=models.CASCADE,
        verbose_name="Norma",
        # Nome para a relação reversa (norma.requisitos.all())
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
        # Garante que um requisito é único para uma norma específica
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

# Novo modelo: Tipos de Questão (dados padronizados)


class TipoQuestao(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name="Nome do Tipo de Questão")
    descricao = models.TextField(verbose_name="Descrição")
    # Se você quiser armazenar a imagem/ícone, precisará de um campo ImageField
    icone = models.ImageField(
        upload_to='icones_tipos_questao/', null=True, blank=True, verbose_name="Ícone")

    class Meta:
        verbose_name = "Tipo de Questão"
        verbose_name_plural = "Tipos de Questão"
        ordering = ['nome']

    def __str__(self):
        return self.nome

# Novo modelo: Modelo de Avaliação (dados padronizados)


class ModeloAvaliacao(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name="Nome do Modelo de Avaliação")
    # Um modelo de avaliação tem muitos tipos de questão
    tipos_questao_suportados = models.ManyToManyField(
        TipoQuestao,
        verbose_name="Tipos de Questão Suportados",
        related_name='modelos_avaliacao'
    )
    descricao = models.TextField(verbose_name="Descrição do Modelo")

    class Meta:
        verbose_name = "Modelo de Avaliação"
        verbose_name_plural = "Modelos de Avaliação"
        ordering = ['nome']

    def __str__(self):
        return self.nome

# Novo modelo: Checklist


class Checklist(models.Model):
    nome = models.CharField(max_length=255, verbose_name="Nome do Checklist")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    # Relações com os modelos padronizados
    # Alterado para ForeignKey, permitindo apenas UMA ferramenta por checklist
    ferramenta = models.ForeignKey(
        FerramentaDigital,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Ferramenta Digital",
        related_name='checklists'
    )
    modelo_avaliacao = models.ForeignKey(
        ModeloAvaliacao,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Modelo de Avaliação",
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
    # Para controle da ordem de exibição
    ordem = models.IntegerField(default=0, verbose_name="Ordem")

    class Meta:
        verbose_name = "Tópico"
        verbose_name_plural = "Tópicos"
        unique_together = ('checklist', 'descricao')
        ordering = ['ordem', 'descricao']

    def __str__(self):
        return self.descricao


# Novo modelo: Pergunta (Item) do Checklist
class Pergunta(models.Model):
    topico = models.ForeignKey(
        Topico,
        on_delete=models.CASCADE,
        verbose_name="Tópico",
        related_name='perguntas'
    )
    descricao = models.TextField(verbose_name="Descrição da Pergunta")

    # Campo para o tipo de questão (Resposta Livre, Apenas Foto, etc.)
    tipo_questao = models.ForeignKey(
        TipoQuestao,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Tipo de Questão",
        related_name='perguntas'
    )

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


# Novo modelo: Opções da Pergunta (para o tipo 'Criar uma Opção')
class OpcaoPergunta(models.Model):
    pergunta = models.ForeignKey(
        'Pergunta',
        on_delete=models.CASCADE,
        verbose_name="Pergunta",
        related_name='opcoes'
    )
    descricao = models.CharField(
        max_length=100, verbose_name="Descrição da Opção")

    tipo_status = models.CharField(
        max_length=20,
        choices=[
            ('CONFORME', 'Conforme'),
            ('NAO_CONFORME', 'Não Conforme'),
            ('NA', 'N/A'),
            ('DESVIO_SOLUCIONADO', 'Desvio Solucionado'),
        ],
        verbose_name="Tipo de Status"
    )

    # Novo campo para instruções do usuário
    instrucoes_usuario = models.TextField(
        null=True, blank=True, verbose_name="Instruções do Usuário")

    class Meta:
        verbose_name = "Opção de Pergunta"
        verbose_name_plural = "Opções de Perguntas"
        unique_together = ('pergunta', 'descricao')

    def __str__(self):
        return self.descricao


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
    # O campo 'ferramenta_causa_raiz' agora é uma ForeignKey
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


###################################################

# Níveis organizacionais (para o campo 'Nivel')
NIVEIS_ORGANIZACIONAIS = [
    ('EMPRESA', 'Empresa'),
    ('AREA', 'Área'),
    ('SETOR', 'Setor'),
    ('SUBSETOR', 'Subsetor'),
]

# Categorias de auditoria (App ou Web)
CATEGORIAS_AUDITORIA = [
    ('APP', 'App'),
    ('WEB', 'Web'),
]

# Frequências de agendamento
FREQUENCIAS_AGENDAMENTO = [
    ('DIARIO', 'Diário'),
    ('SEMANAL', 'Semanal'),
    ('QUINZENAL', 'Quinzenal'),
    ('MENSAL', 'Mensal'),
    ('ANUAL', 'Anual'),
]


class Auditoria(models.Model):
    # Passo 1: Ferramenta
    ferramenta = models.ForeignKey(
        FerramentaDigital,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Ferramenta Digital"
    )

    # Passo 2: Local, Modelo e Ativo
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
    # ForeignKeys para os diferentes níveis organizacionais
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

    # Um agendamento pode ter múltiplos modelos e múltiplos ativos
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
        blank=True,  # Torna o campo opcional
        verbose_name="Turnos"
    )

    # Passo 3: Programação
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

    # Campos de controle
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


class AuditoriaInstancia(models.Model):
    auditoria_agendada = models.ForeignKey(
        Auditoria,
        on_delete=models.CASCADE,
        verbose_name="Auditoria Agendada",
        related_name='instancias'
    )
    data_execucao = models.DateField(verbose_name="Data de Execução")
    executada = models.BooleanField(default=False, verbose_name="Executada?")

    class Meta:
        verbose_name = "Instância de Auditoria"
        verbose_name_plural = "Instâncias de Auditoria"
        ordering = ['data_execucao']

    def __str__(self):
        return f"Execução em {self.data_execucao} de {self.auditoria_agendada}"
