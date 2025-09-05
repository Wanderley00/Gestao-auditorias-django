# clientes/models.py

from django.db import models
# Importar o modelo de Usuário padrão do Django
from django.contrib.auth.models import User
from django.conf import settings


class Cliente(models.Model):
    nome = models.CharField(max_length=200, unique=True,
                            verbose_name="Nome do Cliente")
    # Assumi que NPR é um campo de texto/código
    npr = models.CharField(max_length=50, null=True,
                           blank=True, verbose_name="NPR")
    email = models.EmailField(
        max_length=255, unique=True, null=True, blank=True, verbose_name="E-mail")

    # Relação com o modelo de Usuário padrão do Django
    # Um cliente pode ter um usuário associado (ex: o responsável pelo cliente no sistema)
    usuario_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # Se o usuário for apagado, o campo no cliente fica nulo
        null=True, blank=True,
        verbose_name="Usuário Responsável",
        related_name='clientes_responsavel'  # Nome para a relação reversa
    )

    # Campo para o logo do cliente
    logo_cliente = models.ImageField(
        upload_to='clientes_logos/', null=True, blank=True, verbose_name="Logo do Cliente")

    # Campos de controle
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nome']

    def __str__(self):
        return self.nome
