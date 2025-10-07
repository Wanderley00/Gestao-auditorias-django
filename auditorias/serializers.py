# auditorias/serializers.py

from rest_framework import serializers
from .models import (
    Auditoria, AuditoriaInstancia, Checklist, Topico, Pergunta,
    OpcaoResposta, OpcaoPorcentagem, Resposta, AnexoResposta
)

import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """
    Um campo de serializer que lida com imagens codificadas em Base64.
    """

    def to_internal_value(self, data):
        # Verifica se o dado recebido é uma string e tem o formato Base64
        if isinstance(data, str) and data.startswith('data:image'):
            # Separa o formato do conteúdo Base64
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            # Gera um nome de arquivo único
            file_name = f"{uuid.uuid4()}.{ext}"
            # Decodifica a string Base64 e a transforma em um arquivo que o Django entende
            data = ContentFile(base64.b64decode(imgstr), name=file_name)

        return super().to_internal_value(data)


# --- Serializers para a estrutura do Checklist ---


class OpcaoRespostaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpcaoResposta
        fields = ['id', 'descricao', 'status']


class OpcaoPorcentagemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpcaoPorcentagem
        fields = ['id', 'descricao', 'peso', 'cor']


class PerguntaSerializer(serializers.ModelSerializer):
    opcoes_resposta = OpcaoRespostaSerializer(many=True, read_only=True)
    opcoes_porcentagem = OpcaoPorcentagemSerializer(many=True, read_only=True)

    class Meta:
        model = Pergunta
        fields = [
            'id', 'descricao', 'ordem', 'obrigatoria',
            'resposta_livre', 'foto', 'criar_opcao', 'porcentagem',
            'opcoes_resposta', 'opcoes_porcentagem'
        ]


class TopicoSerializer(serializers.ModelSerializer):
    perguntas = PerguntaSerializer(many=True, read_only=True)

    class Meta:
        model = Topico
        fields = ['id', 'descricao', 'ordem', 'perguntas']


class ChecklistSerializer(serializers.ModelSerializer):
    topicos = TopicoSerializer(many=True, read_only=True)

    class Meta:
        model = Checklist
        fields = ['id', 'nome', 'topicos']


# --- Serializers para a Auditoria (simplificado) ---

class AuditoriaPaiSerializer(serializers.ModelSerializer):
    """ Serializer enriquecido para a Auditoria 'pai' """
    modelo_auditoria_nome = serializers.SerializerMethodField()
    checklist_nome = serializers.SerializerMethodField()
    # NOVO CAMPO: Para o nome do local
    local_nome = serializers.SerializerMethodField()
    # FORMATANDO A DATA
    data_criacao = serializers.DateTimeField(format="%d/%m/%Y", read_only=True)

    class Meta:
        model = Auditoria
        fields = [
            'id',
            'data_criacao',
            'modelo_auditoria_nome',
            'checklist_nome',
            'local_nome',  # Usaremos este campo unificado
        ]

    def get_modelo_auditoria_nome(self, obj):
        primeiro_modelo = obj.modelos.first()
        return primeiro_modelo.descricao if primeiro_modelo else 'N/A'

    def get_checklist_nome(self, obj):
        primeiro_modelo = obj.modelos.first()
        if primeiro_modelo and primeiro_modelo.checklist:
            return primeiro_modelo.checklist.nome
        return 'N/A'

    def get_local_nome(self, obj):
        """
        Retorna o nome do local específico com base no nível organizacional.
        """
        if obj.nivel_organizacional == 'SUBSETOR' and obj.local_subsetor:
            return obj.local_subsetor.nome
        if obj.nivel_organizacional == 'SETOR' and obj.local_setor:
            return obj.local_setor.nome
        if obj.nivel_organizacional == 'AREA' and obj.local_area:
            return obj.local_area.nome
        if obj.nivel_organizacional == 'EMPRESA' and obj.local_empresa:
            return obj.local_empresa.nome
        return 'Local não definido'

# --- Serializer para os Detalhes de UMA Auditoria ---


class AuditoriaInstanciaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para uma única Instância de Auditoria,
    incluindo o checklist completo.
    """
    # Usamos um SerializerMethodField para buscar o checklist de forma customizada
    checklist = serializers.SerializerMethodField()

    class Meta:
        model = AuditoriaInstancia
        fields = ['id', 'data_execucao', 'checklist']

    def get_checklist(self, obj):
        # Uma Auditoria (pai) pode ter vários Modelos, e cada Modelo um Checklist.
        # Para a API, vamos assumir que a instância se refere ao checklist do primeiro modelo associado.
        # Esta lógica pode ser ajustada se a regra de negócio for diferente.
        primeiro_modelo = obj.auditoria_agendada.modelos.first()
        if primeiro_modelo and primeiro_modelo.checklist:
            return ChecklistSerializer(primeiro_modelo.checklist).data
        return None


class AuditoriaInstanciaListSerializer(serializers.ModelSerializer):
    # Esta parte continua a mesma, mas agora o 'auditoria_info' virá com os novos campos
    auditoria_info = AuditoriaPaiSerializer(
        source='auditoria_agendada', read_only=True)

    class Meta:
        model = AuditoriaInstancia
        fields = [
            'id',
            'data_execucao',
            'executada',
            'auditoria_agendada',
            'auditoria_info'
        ]


class RespostaSerializer(serializers.ModelSerializer):
    """
    Serializer para receber, validar e CRIAR os dados de uma única resposta,
    incluindo anexos de fotos.
    """
    pergunta_id = serializers.IntegerField(write_only=True)
    # Novo campo para receber uma lista de imagens em Base64
    anexos_base64 = serializers.ListField(
        child=Base64ImageField(),
        required=False,    # O campo não é obrigatório
        write_only=True    # Usado apenas para receber dados, não para exibir
    )

    class Meta:
        model = Resposta
        fields = [
            'pergunta_id',
            'opcao_resposta',
            'opcao_porcentagem',
            'resposta_livre_texto',
            'anexos_base64',  # Adicione o novo campo aqui
        ]

    def create(self, validated_data):
        # Pega a lista de anexos (fotos) e remove do dicionário principal
        anexos_data = validated_data.pop('anexos_base64', [])

        # Pega a instância da auditoria que passamos da view
        instancia = self.context['auditoria_instancia']

        # Cria o objeto Resposta com os dados restantes
        resposta = Resposta.objects.create(
            auditoria_instancia=instancia,
            **validated_data
        )

        # Se houver anexos, cria os objetos AnexoResposta
        for anexo_file in anexos_data:
            AnexoResposta.objects.create(resposta=resposta, arquivo=anexo_file)

        return resposta
