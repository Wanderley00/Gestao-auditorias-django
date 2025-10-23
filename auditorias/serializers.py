# auditorias/serializers.py

from rest_framework import serializers
from .models import (
    Auditoria, AuditoriaInstancia, Checklist, Topico, Pergunta,
    OpcaoResposta, OpcaoPorcentagem, Resposta, AnexoResposta
)
import base64
import uuid
from django.core.files.base import ContentFile

# --- CAMPO Base64 CORRIGIDO E MELHORADO ---
# Renomeado para Base64FileField para ser mais genérico


class Base64FileField(serializers.FileField):
    """
    Um campo de serializer que lida com arquivos codificados em Base64,
    aceitando tanto o formato raw quanto o formato com prefixo "data:".
    """

    def to_internal_value(self, data):
        # Verifica se o dado é uma string Base64
        if isinstance(data, str):
            # Se tiver o prefixo 'data:[...];base64,', remove-o
            if 'base64,' in data:
                header, data = data.split(';base64,')

            try:
                # Decodifica os dados e cria um ContentFile
                decoded_file = base64.b64decode(data)
                # Gera um nome de arquivo único. Você pode adicionar uma extensão padrão se quiser.
                file_name = str(uuid.uuid4())[:12]
                # Usa o ContentFile que o Django entende
                data = ContentFile(decoded_file, name=f'{file_name}.jpg')
            except (TypeError, ValueError):
                self.fail('invalid_file')

        return super().to_internal_value(data)

# --- O RESTO DOS SERIALIZERS CONTINUA IGUAL ---


class OpcaoRespostaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpcaoResposta
        fields = ['id', 'descricao', 'status']

# ... (outros serializers como OpcaoPorcentagemSerializer, PerguntaSerializer, etc. continuam aqui sem alterações) ...


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


class AuditoriaPaiSerializer(serializers.ModelSerializer):
    """ Serializer enriquecido para a Auditoria 'pai' """
    modelo_auditoria_nome = serializers.SerializerMethodField()
    checklist_nome = serializers.SerializerMethodField()
    local_nome = serializers.SerializerMethodField()
    data_criacao = serializers.DateTimeField(format="%d/%m/%Y", read_only=True)
    ferramenta_nome = serializers.CharField(
        source='ferramenta.nome', read_only=True)
    programacao = serializers.CharField(
        source='get_programacao_display', read_only=True)
    criado_por_nome = serializers.CharField(
        source='criado_por.get_full_name', read_only=True, default='Sistema')

    class Meta:
        model = Auditoria
        fields = [
            'id',
            'data_criacao',
            'modelo_auditoria_nome',
            'checklist_nome',
            'local_nome',
            'ferramenta_nome',
            'programacao',
            'criado_por_nome',
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
        if obj.nivel_organizacional == 'SUBSETOR' and obj.local_subsetor:
            return obj.local_subsetor.nome
        if obj.nivel_organizacional == 'SETOR' and obj.local_setor:
            return obj.local_setor.nome
        if obj.nivel_organizacional == 'AREA' and obj.local_area:
            return obj.local_area.nome
        if obj.nivel_organizacional == 'EMPRESA' and obj.local_empresa:
            return obj.local_empresa.nome
        return 'Local não definido'


class AuditoriaInstanciaDetailSerializer(serializers.ModelSerializer):
    checklist = serializers.SerializerMethodField()

    class Meta:
        model = AuditoriaInstancia
        fields = ['id', 'data_execucao', 'checklist']

    def get_checklist(self, obj):
        if obj.checklist_usado:
            return ChecklistSerializer(obj.checklist_usado).data
        return None


class AuditoriaInstanciaListSerializer(serializers.ModelSerializer):
    auditoria_info = AuditoriaPaiSerializer(
        source='auditoria_agendada', read_only=True)
    status = serializers.CharField(source='status_execucao', read_only=True)

    local_execucao_nome = serializers.CharField(
        source='local_execucao.nome', read_only=True, default='N/A')

    total_perguntas = serializers.IntegerField(
        source='get_total_perguntas', read_only=True)

    class Meta:
        model = AuditoriaInstancia
        fields = [
            'id',
            'data_execucao',
            'executada',
            'status',
            'auditoria_info',
            'local_execucao_nome',
            'total_perguntas',
        ]


class RespostaSerializer(serializers.ModelSerializer):
    pergunta_id = serializers.IntegerField(write_only=True)
    # --- ATUALIZADO: Usando o novo campo Base64FileField ---
    anexos_base64 = serializers.ListField(
        child=Base64FileField(),  # <<<--- MUDANÇA AQUI
        required=False,
        write_only=True
    )

    class Meta:
        model = Resposta
        fields = [
            'pergunta_id',
            'opcao_resposta',
            'opcao_porcentagem',
            'resposta_livre_texto',
            'anexos_base64',
            'oportunidade_melhoria',
            'desvio_solucionado',
            'grau_nc',
            'data_resposta',
        ]

    def create(self, validated_data):
        # --- ADICIONE ESTAS LINHAS PARA DEBUG ---
        # print("--- DADOS VALIDADOS PELO SERIALIZER ---", validated_data)
        anexos_data = validated_data.pop('anexos_base64', [])
        # print("--- ANEXOS ENCONTRADOS ---", "Sim" if anexos_data else "Não")
        # --- FIM DAS LINHAS DE DEBUG ---

        instancia = self.context['auditoria_instancia']

        resposta, created = Resposta.objects.update_or_create(
            auditoria_instancia=instancia,
            pergunta_id=validated_data.get('pergunta_id'),
            defaults=validated_data
        )

        for anexo_file in anexos_data:
            AnexoResposta.objects.create(resposta=resposta, arquivo=anexo_file)

        return resposta
