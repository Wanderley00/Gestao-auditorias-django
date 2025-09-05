# itens/models.py

from django.db import models
# Importar o modelo de Unidade de Medida
from cadastros_base.models import UnidadeMedida


class CategoriaItem(models.Model):
    descricao = models.CharField(
        max_length=100, unique=True, verbose_name="Descrição da Categoria")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Categoria de Item"
        verbose_name_plural = "Categorias de Itens"
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


class SubcategoriaItem(models.Model):
    # Uma subcategoria pertence a uma categoria principal
    categoria = models.ForeignKey(
        CategoriaItem,
        # Se a categoria for apagada, as subcategorias associadas também são
        on_delete=models.CASCADE,
        verbose_name="Categoria Principal",
        # Nome para a relação reversa (categoria.subcategorias.all())
        related_name='subcategorias'
    )
    descricao = models.CharField(
        max_length=100, verbose_name="Descrição da Subcategoria")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Subcategoria de Item"
        verbose_name_plural = "Subcategorias de Itens"
        # Garante que uma subcategoria é única para uma categoria específica
        unique_together = ('categoria', 'descricao')
        ordering = ['categoria__descricao', 'descricao']

    def __str__(self):
        return f"{self.descricao} ({self.categoria.descricao})"


class Almoxarifado(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name="Nome do Almoxarifado")
    endereco = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Endereço")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Almoxarifado"
        verbose_name_plural = "Almoxarifados"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Item(models.Model):
    codigo_interno = models.CharField(
        max_length=50, unique=True, verbose_name="Código Interno")
    codigo_alternativo = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Código Alternativo")
    descricao = models.CharField(max_length=255, verbose_name="Descrição")

    # Relações com outros cadastros base
    unidade_medida = models.ForeignKey(
        UnidadeMedida,
        # Se a unidade de medida for apagada, o campo no item fica nulo
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Unidade de Medida"
    )
    peso = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Peso")
    valor = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor")

    almoxarifado = models.ForeignKey(
        Almoxarifado,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Almoxarifado"
    )

    # Relações com categorias e subcategorias de item.
    # Por enquanto, assumimos que um item tem UMA categoria principal e UMA subcategoria principal.
    # Se precisar de múltiplas, teremos que mudar para ManyToManyField e ajustar a lógica da UI.
    categoria_principal = models.ForeignKey(
        CategoriaItem,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Categoria Principal",
        related_name='itens_por_categoria'
    )
    subcategoria_principal = models.ForeignKey(
        SubcategoriaItem,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Subcategoria Principal",
        related_name='itens_por_subcategoria'
    )

    # Campo para imagem do item (opcional)
    imagem_item = models.ImageField(
        upload_to='itens_imagens/', null=True, blank=True, verbose_name="Imagem do Item")

    # Campos de controle
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Itens"
        ordering = ['codigo_interno']

    def __str__(self):
        return f"{self.codigo_interno} - {self.descricao}"
