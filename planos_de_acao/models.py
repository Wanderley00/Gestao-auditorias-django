# planos_de_acao/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from organizacao.models import Empresa, Area, Setor, SubSetor

# Definição do modelo de Responsáveis de Plano de Ação por Local


class ResponsavelLocal(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Responsável"
    )
    # Relação com os níveis organizacionais
    local_empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, null=True, blank=True)
    local_area = models.ForeignKey(
        Area, on_delete=models.CASCADE, null=True, blank=True)
    local_setor = models.ForeignKey(
        Setor, on_delete=models.CASCADE, null=True, blank=True)
    local_subsetor = models.ForeignKey(
        SubSetor, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = "Responsável por Local"
        verbose_name_plural = "Responsáveis por Local"

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.local_empresa or self.local_area or self.local_setor or self.local_subsetor}"

# Modelos para o Fórum/Chat


class Forum(models.Model):
    nome = models.CharField(max_length=255, verbose_name="Título do Fórum")
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fórum"
        verbose_name_plural = "Fóruns"

    def __str__(self):
        return self.nome


class MensagemForum(models.Model):
    forum = models.ForeignKey(
        Forum, on_delete=models.CASCADE, related_name='mensagens')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.SET_NULL, null=True)
    conteudo = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mensagem de Fórum"
        verbose_name_plural = "Mensagens de Fórum"
        ordering = ['data_envio']

    def __str__(self):
        return f"Mensagem de {self.autor} em {self.data_envio.strftime('%d/%m/%Y %H:%M')}"


# Opções para a Criticidade
CRITICIDADE_CHOICES = [
    ('NC MAIOR', 'Não Conformidade Maior'),
    ('NC MENOR', 'Não Conformidade Menor'),
    ('DESVIO SOLUCIONADO', 'Desvio Solucionado'),
    ('NA', 'N/A'),
]

# Modelo principal para a Não Conformidade / Plano de Ação


class NaoConformidade(models.Model):
    # Campos de identificação
    id_nao_conformidade = models.CharField(
        max_length=50, unique=True, verbose_name="ID Não Conformidade")

    id_formulario = models.ForeignKey(
        'auditorias.AuditoriaInstancia',  # <-- MUDANÇA AQUI
        on_delete=models.CASCADE,
        verbose_name="ID do Formulário"
    )
    titulo = models.ForeignKey(
        'auditorias.Topico',  # <-- MUDANÇA AQUI
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Título"
    )

    # Campos de Ação
    descricao_desvio = models.TextField(verbose_name="Descrição do Desvio")
    acao_corretiva = models.TextField(
        verbose_name="Ação Corretiva", null=True, blank=True)
    responsavel_acao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Responsável pela Ação"
    )
    prazo_conclusao = models.DateField(verbose_name="Prazo de Conclusão")

    # Campos da sua tabela
    perfil_responsavel = models.CharField(
        max_length=100, verbose_name="Perfil")
    forum = models.ForeignKey(
        # Este está OK (mesmo arquivo)
        Forum, on_delete=models.SET_NULL, null=True, blank=True)

    ferramenta = models.ForeignKey(
        'auditorias.FerramentaDigital',  # <-- MUDANÇA AQUI
        on_delete=models.SET_NULL, null=True, blank=True)
    categoria = models.ForeignKey(
        'auditorias.CategoriaAuditoria',  # <-- MUDANÇA AQUI
        on_delete=models.SET_NULL, null=True, blank=True)

    # Adicione os campos de data que estavam faltando
    data_abertura = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Abertura"
    )
    data_encerramento = models.DateTimeField(
        verbose_name="Data de Encerramento",
        null=True,
        blank=True
    )

    # Campo para criticidade
    criticidade = models.CharField(
        max_length=20,
        choices=CRITICIDADE_CHOICES,
        null=True, blank=True,
        verbose_name="Criticidade"
    )

    # Relação com o Local
    local_empresa = models.ForeignKey(
        Empresa, on_delete=models.SET_NULL, null=True, blank=True, related_name='nao_conformidades_empresa')
    local_area = models.ForeignKey(Area, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='nao_conformidades_area')
    local_setor = models.ForeignKey(
        Setor, on_delete=models.SET_NULL, null=True, blank=True, related_name='nao_conformidades_setor')
    local_subsetor = models.ForeignKey(
        SubSetor, on_delete=models.SET_NULL, null=True, blank=True, related_name='nao_conformidades_subsetor')

    analise = models.TextField(null=True, blank=True, verbose_name="Análise")
    ferramentas_auxiliares = models.ManyToManyField(
        'auditorias.FerramentaCausaRaiz',  # <-- MUDANÇA AQUI
        verbose_name="Ferramentas Auxiliares",
        related_name='nao_conformidades',
        blank=True
    )

    class Meta:
        verbose_name = "Não Conformidade"
        verbose_name_plural = "Não Conformidades"
        ordering = ['-data_abertura']

    def __str__(self):
        return f"Não Conformidade {self.id_nao_conformidade}"

    def save(self, *args, **kwargs):
        if not self.data_encerramento:
            self.data_encerramento = self.data_abertura + timedelta(days=7)
        super().save(*args, **kwargs)


class MensagemForum(models.Model):
    forum = models.ForeignKey(
        Forum, on_delete=models.CASCADE, related_name='mensagens')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.SET_NULL, null=True)
    conteudo = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True)

    # --- ADICIONE ESTE CAMPO ---
    editado = models.BooleanField(default=False, verbose_name="Editado")

    class Meta:
        verbose_name = "Mensagem de Fórum"
