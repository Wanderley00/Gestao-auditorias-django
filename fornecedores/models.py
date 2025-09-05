# fornecedores/models.py

from django.db import models
# Importar o modelo de Usuário padrão do Django
from django.contrib.auth.models import User
from django.conf import settings


class Fornecedor(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name="Nome do Fornecedor")
    # Assumi que NPR é um campo de texto/código
    npr = models.CharField(max_length=50, null=True,
                           blank=True, verbose_name="NPR")

    # Relação com o modelo de Usuário padrão do Django
    # Um fornecedor pode ter um usuário associado (ex: o responsável pelo contato com o fornecedor no sistema)
    usuario_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # Se o usuário for apagado, o campo no fornecedor fica nulo
        null=True, blank=True,
        verbose_name="Usuário Responsável",
        related_name='fornecedores_responsavel'  # Nome único para a relação reversa
    )

    # Campos de controle
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['nome']

    def __str__(self):
        return self.nome
