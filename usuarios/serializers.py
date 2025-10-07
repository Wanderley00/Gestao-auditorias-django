# usuarios/serializers.py

from rest_framework import serializers
from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo de Usuário.
    """
    class Meta:
        model = Usuario
        # Define os campos que serão expostos na API
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        # Garante que o username não possa ser alterado via API
        read_only_fields = ['username']


class AlterarSenhaSerializer(serializers.Serializer):
    """
    Serializer para o endpoint de alteração de senha.
    """
    old_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True)
    new_password2 = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Sua senha antiga não foi digitada corretamente. Por favor, tente novamente.")
        return value

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError(
                {"new_password2": "As duas senhas não coincidem."})
        return data

    def save(self, **kwargs):
        password = self.validated_data['new_password1']
        user = self.context['request'].user
        user.set_password(password)
        user.save()
        return user
