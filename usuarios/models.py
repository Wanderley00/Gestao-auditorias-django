# usuarios/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from fornecedores.models import Fornecedor  # Importe o modelo de Fornecedor


class Usuario(AbstractUser):
    # Campos personalizados
    registro = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Nº de Registro"
    )

    # Relacionamento com Fornecedores
    fornecedores = models.ManyToManyField(
        Fornecedor,
        blank=True,
        verbose_name="Fornecedores com Acesso",
        related_name="usuarios_com_acesso"
    )

    # Acesso a permissões e grupos já é incluído com o AbstractUser

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
