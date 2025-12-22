# auditorias/serializers.py

from rest_framework import serializers
from .models import (
    Auditoria, AuditoriaInstancia, Checklist, Topico, Pergunta,
    OpcaoResposta, OpcaoPorcentagem, Resposta, AnexoResposta, PlanoDeAcao
)
import base64
import uuid
from django.core.files.base import ContentFile
from django.utils import timezone

from planos_de_acao.models import Forum

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

    # Precisamos do ID para saber se a auditoria é "flutuante" (null)
    local_execucao_id = serializers.IntegerField(
        source='local_execucao.id', read_only=True, allow_null=True)

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
            'local_execucao_id',
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
            # --- CAMPOS ADICIONADOS ---
            'descricao_oportunidade_melhoria',
            'descricao_desvio_solucionado',
            'descricao_desvio_nao_solucionado',
            # --- FIM DOS CAMPOS ADICIONADOS ---
        ]

    def create(self, validated_data):
        anexos_data = validated_data.pop('anexos_base64', [])
        instancia = self.context['auditoria_instancia']

        resposta, created = Resposta.objects.update_or_create(
            auditoria_instancia=instancia,
            pergunta_id=validated_data.get('pergunta_id'),
            defaults=validated_data
        )

        for anexo_file in anexos_data:
            AnexoResposta.objects.create(resposta=resposta, arquivo=anexo_file)

        # --- LÓGICA PARA CRIAR O PLANO DE AÇÃO ---
        self.criar_plano_de_acao_se_necessario(resposta)
        # --- FIM DA LÓGICA ---

        return resposta

    def criar_plano_de_acao_se_necessario(self, resposta):
        """
        Verifica a resposta e cria um Plano de Ação se for uma
        Não Conformidade (e não tiver sido solucionada) ou Oportunidade de Melhoria.
        """
        instancia = resposta.auditoria_instancia
        agendamento = instancia.auditoria_agendada

        tipo_plano = None

        # 1. Verifica se é Não Conformidade
        if resposta.opcao_resposta and resposta.opcao_resposta.status == 'NAO_CONFORME':
            # --- CORREÇÃO AQUI ---
            # Só cria o plano se o desvio NÃO foi solucionado na hora
            if not resposta.desvio_solucionado:
                tipo_plano = 'NAO_CONFORMIDADE'
            # ---------------------

        # 2. Verifica se é Oportunidade de Melhoria
        elif resposta.oportunidade_melhoria == True:
            tipo_plano = 'OPORTUNIDADE_MELHORIA'

        if tipo_plano:
            # Pega a categoria do primeiro modelo (pode ajustar se houver múltiplos)
            categoria_auditoria = None
            primeiro_modelo = agendamento.modelos.first()
            if primeiro_modelo:
                categoria_auditoria = primeiro_modelo.categoria

            # Busca o responsável pela ação com base no local de execução
            responsavel_do_local = None
            if instancia.local_execucao:
                responsavel_do_local = instancia.local_execucao.usuario_responsavel

            # Verifica se já existe um plano (e, por extensão, um fórum)
            plano_existente = PlanoDeAcao.objects.filter(
                origem_resposta=resposta).first()

            # Se o plano não existir, crie um novo fórum para ele
            if not plano_existente:
                novo_forum = Forum.objects.create(
                    nome=f"Discussão Plano #{resposta.pergunta.descricao[:50]}..."
                )
            else:
                novo_forum = plano_existente.forum  # Reutiliza o fórum existente

            # Cria ou atualiza o plano de ação
            PlanoDeAcao.objects.update_or_create(
                origem_resposta=resposta,
                defaults={
                    'tipo': tipo_plano,
                    'titulo': resposta.pergunta.descricao,
                    'local_execucao': instancia.local_execucao,
                    'ferramenta': agendamento.ferramenta,
                    'categoria': categoria_auditoria,
                    'data_abertura': resposta.data_resposta or timezone.now(),
                    'responsavel_acao': responsavel_do_local,
                    'forum': novo_forum
                }
            )

        # 3. Se a resposta foi corrigida (não é mais NC nem Oportunidade)
        # OU SE FOI MARCADO COMO DESVIO SOLUCIONADO (tipo_plano continuará None)
        # e um plano já existia, devemos excluí-lo.
        elif not tipo_plano:
            # Encontra e deleta qualquer plano de ação obsoleto
            PlanoDeAcao.objects.filter(origem_resposta=resposta).delete()
