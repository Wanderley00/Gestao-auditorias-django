# organizacao/models.py

from django.db import models
from django.conf import settings


class Empresa(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name="Nome da Empresa")
    cnpj = models.CharField(max_length=18, unique=True,
                            null=True, blank=True, verbose_name="CNPJ")
    endereco = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Endereço")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")
    # Novo campo para o responsável
    usuario_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Usuário Responsável",
        related_name='empresas_responsavel'
    )

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Area(models.Model):
    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    nome = models.CharField(max_length=100, verbose_name="Nome da Área")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")
    # Novo campo para o responsável
    usuario_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Usuário Responsável",
        related_name='areas_responsavel'
    )

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"
        unique_together = ('empresa', 'nome')
        ordering = ['empresa__nome', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.empresa.nome})"


class Setor(models.Model):
    area = models.ForeignKey(
        Area, on_delete=models.CASCADE, verbose_name="Área")
    nome = models.CharField(max_length=100, verbose_name="Nome do Setor")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")
    # Novo campo para o responsável
    usuario_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Usuário Responsável",
        related_name='setores_responsavel'
    )

    class Meta:
        verbose_name = "Setor"
        verbose_name_plural = "Setores"
        unique_together = ('area', 'nome')
        ordering = ['area__empresa__nome', 'area__nome', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.area.nome} - {self.area.empresa.nome})"


class SubSetor(models.Model):
    setor = models.ForeignKey(
        Setor, on_delete=models.CASCADE, verbose_name="Setor")
    nome = models.CharField(max_length=100, verbose_name="Nome do Subsetor")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")
    # Novo campo para o responsável
    usuario_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Usuário Responsável",
        related_name='subsetores_responsavel'
    )

    class Meta:
        verbose_name = "Subsetor"
        verbose_name_plural = "Subsetores"
        unique_together = ('setor', 'nome')
        ordering = ['setor__area__empresa__nome',
                    'setor__area__nome', 'setor__nome', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.setor.nome} - {self.setor.area.nome})"
