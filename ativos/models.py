# ativos/models.py

from django.db import models
# Importar o SubSetor para a Estrutura Organizacional
from organizacao.models import SubSetor


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name="Nome da Categoria")
    descricao = models.TextField(
        null=True, blank=True, verbose_name="Descrição")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Marca(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name="Nome da Marca")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Modelo(models.Model):
    marca = models.ForeignKey(
        Marca, on_delete=models.CASCADE, verbose_name="Marca")
    nome = models.CharField(max_length=100, verbose_name="Nome do Modelo")
    descricao = models.TextField(
        null=True, blank=True, verbose_name="Descrição Detalhada")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Modelo"
        verbose_name_plural = "Modelos"
        # Garante que um modelo é único para uma marca
        unique_together = ('marca', 'nome')
        ordering = ['marca__nome', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.marca.nome})"


class Ativo(models.Model):
    tag = models.CharField(max_length=50, unique=True,
                           verbose_name="Tag do Ativo")
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    custo = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Custo")
    codigo_fabricante = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Código do Fabricante")

    # Relações com outros modelos - ADICIONAR related_name AQUI
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Categoria",
        related_name='ativos_categoria'  # <-- Nome único para a relação reversa
    )
    marca = models.ForeignKey(
        Marca,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Marca",
        related_name='ativos_marca'  # <-- Nome único
    )
    modelo = models.ForeignKey(
        Modelo,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Modelo",
        related_name='ativos_modelo'  # <-- Nome único
    )
    estrutura_organizacional = models.ForeignKey(
        SubSetor,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Estrutura Organizacional (Subsetor)",
        related_name='ativos_subsetor'  # <-- Nome único (e claro)
    )

    # Campos de controle
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    # Campo para imagem do ativo
    imagem_ativo = models.ImageField(
        upload_to='ativos_imagens/', null=True, blank=True, verbose_name="Imagem do Ativo")

    class Meta:
        verbose_name = "Ativo"
        verbose_name_plural = "Ativos"
        ordering = ['tag']

    def __str__(self):
        return f"{self.tag} - {self.descricao}"
