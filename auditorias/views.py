# auditorias/views.py

from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import csv
from django.http import HttpResponse
from django.db.models import Q, Count
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .serializers import RespostaSerializer

from planos_de_acao.models import Forum, MensagemForum

from django.views.decorators.http import require_POST

# Altere ListAPIView para incluir RetrieveAPIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
# Altere a importação dos serializers
from .serializers import AuditoriaInstanciaListSerializer, AuditoriaInstanciaDetailSerializer

from .models import (
    Pilar, CategoriaAuditoria, Norma, RequisitoNorma, FerramentaDigital,
    Checklist, Topico, Pergunta, OpcaoResposta, OpcaoPorcentagem,
    FerramentaCausaRaiz, ModeloAuditoria, Auditoria, AuditoriaInstancia, Resposta,
    CATEGORIAS_AUDITORIA, PlanoDeAcao, Investimento, EvidenciaPlano, HistoricoPlanoAcao
)
from organizacao.models import Empresa, Area, Setor, SubSetor
from ativos.models import Ativo
from cadastros_base.models import Turno
from usuarios.models import Usuario

from django.db.models import Min, Max
from django.db.models import Max, Q
from django.db.models import Q, F, Value
from django.db.models.functions import Concat

from django.utils import timezone

from django.db import transaction

from django.db.models.functions import TruncMonth
from django.db.models import Count, Q

import json

from calendar import monthrange
from datetime import date

# ============================================================================
# VIEWS PRINCIPAIS - DASHBOARD E LISTAGENS
# ============================================================================


def registrar_historico(plano, usuario, descricao, tipo='STATUS'):
    """Função auxiliar para registrar eventos no histórico."""
    HistoricoPlanoAcao.objects.create(
        plano=plano,
        usuario=usuario,
        descricao=descricao,
        tipo=tipo
    )


@login_required
def dashboard_auditorias(request):
    # 1. Filtros Básicos (Por padrão, ano atual)
    ano_atual = timezone.now().year
    qs_instancias = AuditoriaInstancia.objects.filter(
        data_execucao__year=ano_atual)

    # 2. KPIs Principais
    total_planejadas = qs_instancias.count()
    total_realizadas = qs_instancias.filter(executada=True).count()

    eficiencia = 0
    if total_planejadas > 0:
        eficiencia = (total_realizadas / total_planejadas) * 100

    # Total de Itens Não Conformes (Respostas NC em auditorias deste ano)
    total_nc = Resposta.objects.filter(
        auditoria_instancia__in=qs_instancias,
        opcao_resposta__status='NAO_CONFORME'
    ).count()

    # 3. Gráfico: Planejado vs Realizado por Mês (Barras Agrupadas)
    dados_mensais = qs_instancias.annotate(
        mes=TruncMonth('data_execucao')
    ).values('mes').annotate(
        planejado=Count('id'),
        realizado=Count('id', filter=Q(executada=True))
    ).order_by('mes')

    # Jan, Fev...
    meses_labels = [d['mes'].strftime('%b') for d in dados_mensais]
    series_planejado = [d['planejado'] for d in dados_mensais]
    series_realizado = [d['realizado'] for d in dados_mensais]

    # 4. Gráfico: Auditorias por Local (Top 10)
    # Tenta pegar o subsetor, se não tiver, pega o setor
    locais_data = qs_instancias.values(
        'local_execucao__nome'
    ).annotate(qtd=Count('id')).order_by('-qtd')[:10]

    # Limpeza de nomes (trata auditorias sem local definido ainda)
    locais_labels = [l['local_execucao__nome'] if l['local_execucao__nome']
                     else 'Não Definido' for l in locais_data]
    locais_series = [l['qtd'] for l in locais_data]

    # 5. Gráfico: Conformidade Geral (Pizza)
    # Conta total de respostas avaliadas no período
    total_respostas = Resposta.objects.filter(
        auditoria_instancia__in=qs_instancias).count()
    total_respostas_nc = Resposta.objects.filter(
        auditoria_instancia__in=qs_instancias,
        opcao_resposta__status='NAO_CONFORME'
    ).count()

    total_conforme = total_respostas - total_respostas_nc

    # Evita gráfico vazio
    if total_respostas == 0:
        series_conformidade = [0, 0]
    else:
        series_conformidade = [total_conforme, total_respostas_nc]

    # 6. Tabela: Próximas Auditorias (Agenda)
    proximas_auditorias = qs_instancias.filter(
        executada=False,
        data_execucao__gte=timezone.now().date()
    ).select_related('responsavel', 'auditoria_agendada__ferramenta').order_by('data_execucao')[:5]

    context = {
        'title': f'Dashboard de Auditorias {ano_atual}',

        # KPIs
        'kpi_realizadas': total_realizadas,
        'kpi_planejadas': total_planejadas,
        'kpi_eficiencia': f"{eficiencia:.1f}".replace('.', ','),
        'kpi_nc': total_nc,

        # Listas
        'proximas_auditorias': proximas_auditorias,

        # Dados Gráficos
        'chart_meses_labels': json.dumps(meses_labels),
        'chart_series_planejado': json.dumps(series_planejado),
        'chart_series_realizado': json.dumps(series_realizado),

        'chart_locais_labels': json.dumps(locais_labels),
        'chart_locais_series': json.dumps(locais_series),

        'chart_conformidade_series': json.dumps(series_conformidade),
    }

    return render(request, 'auditorias/dashboard.html', context)


# ============================================================================
# VIEWS PARA PILARES
# ============================================================================

@login_required
def lista_pilares(request):
    """Lista todos os pilares com busca e paginação"""
    search = request.GET.get('search', '')
    pilares = Pilar.objects.all()

    if search:
        pilares = pilares.filter(
            Q(nome__icontains=search) | Q(descricao__icontains=search)
        )

    paginator = Paginator(pilares, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Pilares',
        'singular': 'Pilar',
        'button_text': 'Novo Pilar',
        'create_url': 'auditorias:criar_pilar',
        'export_url': 'auditorias:exportar_pilares_csv',  # NOVO
        'artigo': 'o',
        'empty_message': 'Nenhum pilar cadastrado',
        'empty_subtitle': 'Comece criando o primeiro pilar.'
    }
    return render(request, 'auditorias/pilares/lista.html', context)


@login_required
def criar_pilar(request):
    """Cria um novo pilar"""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao', '')
        ativo = request.POST.get('ativo') == 'on'

        if nome:
            try:
                Pilar.objects.create(
                    nome=nome,
                    descricao=descricao,
                    ativo=ativo
                )
                messages.success(request, 'Pilar criado com sucesso!')
                return redirect('auditorias:lista_pilares')
            except Exception as e:
                messages.error(request, f'Erro ao criar pilar: {repr(e)}')
        else:
            messages.error(request, 'Nome é obrigatório!')

    context = {
        'title': 'Criar Pilar',
        'back_url': 'auditorias:lista_pilares'
    }
    return render(request, 'auditorias/pilares/form.html', context)


@login_required
def editar_pilar(request, pk):
    """Edita um pilar existente"""
    pilar = get_object_or_404(Pilar, pk=pk)

    if request.method == 'POST':
        pilar.nome = request.POST.get('nome')
        pilar.descricao = request.POST.get('descricao', '')
        pilar.ativo = request.POST.get('ativo') == 'on'

        try:
            pilar.save()
            messages.success(request, 'Pilar atualizado com sucesso!')
            return redirect('auditorias:lista_pilares')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar pilar: {repr(e)}')

    context = {
        'pilar': pilar,
        'title': 'Editar Pilar',
        'back_url': 'auditorias:lista_pilares'
    }
    return render(request, 'auditorias/pilares/form.html', context)


@login_required
def deletar_pilar(request, pk):
    """Deleta um pilar"""
    pilar = get_object_or_404(Pilar, pk=pk)

    if request.method == 'POST':
        try:
            pilar.delete()
            messages.success(request, 'Pilar deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar pilar: {repr(e)}')
        return redirect('auditorias:lista_pilares')

    context = {
        'object': pilar,
        'title': 'Pilar'
    }
    return render(request, 'auditorias/deletar_generico.html', context)


@login_required
def exportar_pilares_csv(request):
    response = HttpResponse(
        content_type='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': 'attachment; filename="pilares.csv"'}
    )

    writer = csv.writer(response)
    writer.writerow(['Nome', 'Descrição', 'Status', 'Data de Cadastro'])

    search = request.GET.get('search', '')
    pilares = Pilar.objects.all()
    if search:
        pilares = pilares.filter(
            Q(nome__icontains=search) | Q(descricao__icontains=search))

    for pilar in pilares:
        writer.writerow([
            pilar.nome,
            pilar.descricao,
            'Ativo' if pilar.ativo else 'Inativo',
            pilar.data_cadastro.strftime('%d/%m/%Y %H:%M')
        ])

    return response

# ============================================================================
# VIEWS PARA CATEGORias DE AUDITORIA
# ============================================================================


@login_required
def lista_categorias_auditoria(request):
    """Lista todas as categorias de auditoria"""
    search = request.GET.get('search', '')
    categorias = CategoriaAuditoria.objects.select_related('pilar').all()

    if search:
        categorias = categorias.filter(
            Q(descricao__icontains=search) | Q(pilar__nome__icontains=search)
        )

    paginator = Paginator(categorias, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Categorias de Auditoria',
        'singular': 'Categoria de Auditoria',
        'button_text': 'Nova Categoria de Auditoria',
        'create_url': 'auditorias:criar_categoria_auditoria',
        'export_url': 'auditorias:exportar_categorias_auditoria_csv',  # NOVO
        'artigo': 'a',
        'empty_message': 'Nenhuma categoria de auditoria cadastrada',
        'empty_subtitle': 'Comece criando a primeira categoria de auditoria.'
    }
    return render(request, 'auditorias/categorias/lista.html', context)


@login_required
def criar_categoria_auditoria(request):
    """Cria uma nova categoria de auditoria"""
    if request.method == 'POST':
        pilar_id = request.POST.get('pilar')
        descricao = request.POST.get('descricao')
        ativo = request.POST.get('ativo') == 'on'

        if pilar_id and descricao:
            try:
                pilar = Pilar.objects.get(pk=pilar_id)
                CategoriaAuditoria.objects.create(
                    pilar=pilar,
                    descricao=descricao,
                    ativo=ativo
                )
                messages.success(request, 'Categoria criada com sucesso!')
                return redirect('auditorias:lista_categorias_auditoria')
            except Exception as e:
                messages.error(request, f'Erro ao criar categoria: {repr(e)}')
        else:
            messages.error(request, 'Pilar e descrição são obrigatórios!')

    context = {
        'pilares': Pilar.objects.filter(ativo=True),
        'title': 'Criar Categoria de Auditoria',
        'back_url': 'auditorias:lista_categorias_auditoria'
    }
    return render(request, 'auditorias/categorias/form.html', context)


@login_required
def editar_categoria_auditoria(request, pk):
    """Edita uma categoria de auditoria existente"""
    categoria = get_object_or_404(CategoriaAuditoria, pk=pk)

    if request.method == 'POST':
        pilar_id = request.POST.get('pilar')
        categoria.descricao = request.POST.get('descricao')
        categoria.ativo = request.POST.get('ativo') == 'on'

        if pilar_id:
            categoria.pilar = Pilar.objects.get(pk=pilar_id)

        try:
            categoria.save()
            messages.success(request, 'Categoria atualizada com sucesso!')
            return redirect('auditorias:lista_categorias_auditoria')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar categoria: {repr(e)}')

    context = {
        'categoria': categoria,
        'pilares': Pilar.objects.filter(ativo=True),
        'title': 'Editar Categoria de Auditoria',
        'back_url': 'auditorias:lista_categorias_auditoria'
    }
    return render(request, 'auditorias/categorias/form.html', context)


@login_required
def deletar_categoria_auditoria(request, pk):
    """Deleta uma categoria de auditoria"""
    categoria = get_object_or_404(CategoriaAuditoria, pk=pk)

    if request.method == 'POST':
        try:
            categoria.delete()
            messages.success(request, 'Categoria deletada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar categoria: {repr(e)}')
        return redirect('auditorias:lista_categorias_auditoria')

    context = {
        'object': categoria,
        'title': 'Categoria de Auditoria'
    }
    return render(request, 'auditorias/deletar_generico.html', context)


@login_required
def exportar_categorias_auditoria_csv(request):
    response = HttpResponse(
        content_type='text/csv; charset=utf-8-sig',
        headers={
            'Content-Disposition': 'attachment; filename="categorias_auditoria.csv"'}
    )

    writer = csv.writer(response)
    writer.writerow(['Descrição', 'Pilar', 'Status', 'Data de Cadastro'])

    search = request.GET.get('search', '')
    categorias = CategoriaAuditoria.objects.select_related('pilar').all()
    if search:
        categorias = categorias.filter(
            Q(descricao__icontains=search) | Q(pilar__nome__icontains=search))

    for cat in categorias:
        writer.writerow([
            cat.descricao,
            cat.pilar.nome if cat.pilar else 'N/A',
            'Ativo' if cat.ativo else 'Inativo',
            cat.data_cadastro.strftime('%d/%m/%Y %H:%M')
        ])

    return response


# ============================================================================
# VIEWS PARA NORMAS
# ============================================================================

@login_required
def lista_normas(request):
    """Lista todas as normas"""
    search = request.GET.get('search', '')
    normas = Norma.objects.all()

    if search:
        normas = normas.filter(
            Q(descricao__icontains=search) | Q(revisao__icontains=search)
        )

    paginator = Paginator(normas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Normas',
        'singular': 'Norma',
        'button_text': 'Nova Norma',
        'create_url': 'auditorias:criar_norma',
        'export_url': 'auditorias:exportar_normas_csv',  # NOVO
        'artigo': 'a',
        'empty_message': 'Nenhuma norma cadastrada',
        'empty_subtitle': 'Comece criando a primeira norma.'
    }
    return render(request, 'auditorias/normas/lista.html', context)


@login_required
def criar_norma(request):
    """Cria uma nova norma"""
    if request.method == 'POST':
        descricao = request.POST.get('descricao')
        revisao = request.POST.get('revisao')
        ativo = request.POST.get('ativo') == 'on'

        if descricao and revisao:
            try:
                Norma.objects.create(
                    descricao=descricao,
                    revisao=revisao,
                    ativo=ativo
                )
                messages.success(request, 'Norma criada com sucesso!')
                return redirect('auditorias:lista_normas')
            except Exception as e:
                messages.error(request, f'Erro ao criar norma: {repr(e)}')
        else:
            messages.error(request, 'Descrição e revisão são obrigatórios!')

    context = {
        'title': 'Criar Norma',
        'back_url': 'auditorias:lista_normas'
    }
    return render(request, 'auditorias/normas/form.html', context)


@login_required
def editar_norma(request, pk):
    """Edita uma norma existente"""
    norma = get_object_or_404(Norma, pk=pk)

    if request.method == 'POST':
        norma.descricao = request.POST.get('descricao')
        norma.revisao = request.POST.get('revisao')
        norma.ativo = request.POST.get('ativo') == 'on'

        try:
            norma.save()
            messages.success(request, 'Norma atualizada com sucesso!')
            return redirect('auditorias:lista_normas')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar norma: {repr(e)}')

    context = {
        'norma': norma,
        'title': 'Editar Norma',
        'back_url': 'auditorias:lista_normas'
    }
    return render(request, 'auditorias/normas/form.html', context)


@login_required
def deletar_norma(request, pk):
    """Deleta uma norma"""
    norma = get_object_or_404(Norma, pk=pk)

    if request.method == 'POST':
        try:
            norma.delete()
            messages.success(request, 'Norma deletada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar norma: {repr(e)}')
        return redirect('auditorias:lista_normas')

    context = {
        'object': norma,
        'title': 'Norma'
    }
    return render(request, 'auditorias/deletar_generico.html', context)


@login_required
def exportar_normas_csv(request):
    response = HttpResponse(
        content_type='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': 'attachment; filename="normas.csv"'}
    )

    writer = csv.writer(response)
    writer.writerow(['Descrição', 'Revisão', 'Status'])

    search = request.GET.get('search', '')
    normas = Norma.objects.all()
    if search:
        normas = normas.filter(Q(descricao__icontains=search)
                               | Q(revisao__icontains=search))

    for norma in normas:
        writer.writerow([
            norma.descricao,
            norma.revisao,
            'Ativo' if norma.ativo else 'Inativo'
        ])

    return response

# ============================================================================
# VIEWS PARA FERRAMENTAS DIGITAIS
# ============================================================================


@login_required
def lista_ferramentas_digitais(request):
    """Lista todas as ferramentas digitais"""
    search = request.GET.get('search', '')
    ferramentas = FerramentaDigital.objects.all()

    if search:
        ferramentas = ferramentas.filter(nome__icontains=search)

    paginator = Paginator(ferramentas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Ferramentas Digitais',
        'singular': 'Ferramenta Digital',
        'button_text': 'Nova Ferramenta Digital',
        'create_url': 'auditorias:criar_ferramenta_digital',
        'export_url': 'auditorias:exportar_ferramentas_digitais_csv',  # NOVO
        'artigo': 'a',
        'empty_message': 'Nenhuma ferramenta digital cadastrada',
        'empty_subtitle': 'Comece criando a primeira ferramenta digital.'
    }
    return render(request, 'auditorias/ferramentas_digitais/lista.html', context)


@login_required
def criar_ferramenta_digital(request):
    """Cria uma nova ferramenta digital"""
    if request.method == 'POST':
        nome = request.POST.get('nome')

        if nome:
            try:
                FerramentaDigital.objects.create(nome=nome)
                messages.success(
                    request, 'Ferramenta digital criada com sucesso!')
                return redirect('auditorias:lista_ferramentas_digitais')
            except Exception as e:
                messages.error(request, f'Erro ao criar ferramenta: {repr(e)}')
        else:
            messages.error(request, 'Nome é obrigatório!')

    context = {
        'title': 'Criar Ferramenta Digital',
        'back_url': 'auditorias:lista_ferramentas_digitais'
    }
    return render(request, 'auditorias/ferramentas_digitais/form.html', context)


@login_required
def editar_ferramenta_digital(request, pk):
    """Edita uma ferramenta digital existente"""
    ferramenta = get_object_or_404(FerramentaDigital, pk=pk)

    if request.method == 'POST':
        ferramenta.nome = request.POST.get('nome')

        try:
            ferramenta.save()
            messages.success(
                request, 'Ferramenta digital atualizada com sucesso!')
            return redirect('auditorias:lista_ferramentas_digitais')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar ferramenta: {repr(e)}')

    context = {
        'ferramenta': ferramenta,
        'title': 'Editar Ferramenta Digital',
        'back_url': 'auditorias:lista_ferramentas_digitais'
    }
    return render(request, 'auditorias/ferramentas_digitais/form.html', context)


@login_required
def deletar_ferramenta_digital(request, pk):
    """Deleta uma ferramenta digital"""
    ferramenta = get_object_or_404(FerramentaDigital, pk=pk)

    if request.method == 'POST':
        try:
            ferramenta.delete()
            messages.success(
                request, 'Ferramenta digital deletada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar ferramenta: {repr(e)}')
        return redirect('auditorias:lista_ferramentas_digitais')

    context = {
        'object': ferramenta,
        'title': 'Ferramenta Digital'
    }
    return render(request, 'auditorias/deletar_generico.html', context)


@login_required
def exportar_ferramentas_digitais_csv(request):
    response = HttpResponse(
        content_type='text/csv; charset=utf-8-sig',
        headers={
            'Content-Disposition': 'attachment; filename="ferramentas_digitais.csv"'}
    )

    writer = csv.writer(response)
    writer.writerow(['Nome'])

    search = request.GET.get('search', '')
    ferramentas = FerramentaDigital.objects.all()
    if search:
        ferramentas = ferramentas.filter(nome__icontains=search)

    for ferramenta in ferramentas:
        writer.writerow([ferramenta.nome])

    return response


# ============================================================================
# VIEWS PARA CHECKLISTS
# ============================================================================

@login_required
def lista_checklists(request):
    """Lista todos os checklists (apenas a versão mais recente de cada)."""
    search = request.GET.get('search', '')
    # --- ALTERAÇÃO AQUI ---
    checklists = Checklist.objects.select_related(
        'ferramenta').filter(is_latest=True)

    if search:
        checklists = checklists.filter(nome__icontains=search)

    paginator = Paginator(checklists, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Checklists',
        'create_url': 'auditorias:criar_checklist',
        'export_url': 'auditorias:exportar_checklists_csv',  # NOVO
    }
    return render(request, 'auditorias/checklists/lista.html', context)


@login_required
def criar_checklist(request):
    """Cria um novo checklist com estrutura completa."""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        ferramenta_id = request.POST.get('ferramenta')
        ativo = request.POST.get('ativo') == 'on'

        if nome:
            try:
                # Criar o checklist básico
                checklist = Checklist.objects.create(
                    nome=nome,
                    ativo=ativo
                )

                if ferramenta_id:
                    checklist.ferramenta_id = ferramenta_id
                    checklist.save()

                # Processar tópicos e perguntas
                processar_estrutura_checklist(request, checklist)

                messages.success(request, 'Checklist criado com sucesso!')
                return redirect('auditorias:lista_checklists')
            except Exception as e:
                messages.error(request, f'Erro ao criar checklist: {repr(e)}')
                import traceback
                print(traceback.format_exc())
        else:
            messages.error(request, 'Nome é obrigatório!')

    context = {
        'ferramentas': FerramentaDigital.objects.all(),
        'status_opcoes': OpcaoResposta._meta.get_field('status').choices,
        'title': 'Criar Checklist',
        'back_url': 'auditorias:lista_checklists'
    }
    return render(request, 'auditorias/checklists/form.html', context)


def _create_new_version_from_request(request, checklist_original):
    """
    Cria uma nova versão de um checklist, garantindo que o número da versão
    seja sempre o próximo da sequência, independentemente de qual versão foi editada.
    """
    # --- INÍCIO DA CORREÇÃO ---
    # 1. Encontra o checklist "pai" (a primeira versão) para agrupar todas as versões.
    base_checklist = checklist_original.original_checklist or checklist_original

    # 2. Encontra o número da versão mais alta existente para este checklist.
    latest_version_number = Checklist.objects.filter(
        Q(pk=base_checklist.pk) | Q(original_checklist=base_checklist)
    ).aggregate(max_version=Max('version'))['max_version'] or 0

    # 3. O número da nova versão será o mais alto + 1 (ex: se o max for 2, a nova será 3).
    new_version_number = latest_version_number + 1
    # --- FIM DA CORREÇÃO ---

    # 4. Cria o novo objeto Checklist com o número de versão correto.
    nova_versao = Checklist.objects.create(
        nome=request.POST.get('nome'),
        ativo=request.POST.get('ativo') == 'on',
        ferramenta_id=request.POST.get('ferramenta') or None,
        version=new_version_number,  # <-- CORRIGIDO
        is_latest=True,
        original_checklist=base_checklist
    )

    # (O restante da função para copiar os tópicos e perguntas continua o mesmo)
    # ... (código existente para processar a estrutura do checklist)
    topicos_data = {}
    for key in request.POST:
        if key.startswith('topico-descricao['):
            topico_id_form = key.split('[')[1].split(']')[0]
            topicos_data[topico_id_form] = {
                'descricao': request.POST.get(key),
                'ordem': request.POST.get(f'topico-ordem[{topico_id_form}]', 0)
            }

    for topico_id_form, topico_info in topicos_data.items():
        novo_topico = Topico.objects.create(
            checklist=nova_versao,
            descricao=topico_info['descricao'],
            ordem=int(topico_info['ordem']) if topico_info['ordem'] else 0
        )

        for key in request.POST:
            if key.startswith(f'pergunta-descricao[{topico_id_form}-'):
                pergunta_id_full = key.split('[')[1].split(']')[0]
                nova_pergunta = Pergunta.objects.create(
                    topico=novo_topico,
                    descricao=request.POST.get(key),
                    ordem=int(request.POST.get(
                        f'pergunta-ordem[{pergunta_id_full}]', 0)),
                    obrigatoria=request.POST.get(
                        f'pergunta-obrigatorio[{pergunta_id_full}]') == 'on',
                    resposta_livre=request.POST.get(
                        f'pergunta-resposta_livre[{pergunta_id_full}]') == 'on',
                    foto=request.POST.get(
                        f'pergunta-foto[{pergunta_id_full}]') == 'on',
                    criar_opcao=request.POST.get(
                        f'pergunta-criar_opcao[{pergunta_id_full}]') == 'on',
                    porcentagem=request.POST.get(
                        f'pergunta-porcentagem[{pergunta_id_full}]') == 'on'
                )

                for opt_key in request.POST:
                    if opt_key.startswith(f'opcao-resposta-descricao[{pergunta_id_full}-'):
                        opt_id_full = opt_key.split('[')[1].split(']')[
                            0]
                        OpcaoResposta.objects.create(
                            pergunta=nova_pergunta,
                            descricao=request.POST.get(opt_key),
                            status=request.POST.get(
                                f'opcao-resposta-status[{opt_id_full}]', 'CONFORME')
                        )

                for opt_key in request.POST:
                    if opt_key.startswith(f'opcao-porcentagem-descricao[{pergunta_id_full}-'):
                        opt_id_full = opt_key.split('[')[1].split(']')[
                            0]
                        OpcaoPorcentagem.objects.create(
                            pergunta=nova_pergunta,
                            descricao=request.POST.get(opt_key),
                            peso=int(request.POST.get(
                                f'opcao-porcentagem-peso[{opt_id_full}]', 0)),
                            cor=request.POST.get(
                                f'opcao-porcentagem-cor[{opt_id_full}]', '#FFFFFF')
                        )

    return nova_versao


@login_required
def editar_checklist(request, pk):
    """
    Ao editar um checklist, cria uma nova versão (clone) com as modificações
    e atualiza as auditorias futuras. A nova versão será sempre a mais recente.
    """
    checklist_a_ser_editado = get_object_or_404(Checklist, pk=pk)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # --- INÍCIO DA CORREÇÃO ---
                # 1. Encontra o checklist "pai" e a versão que é atualmente a mais recente.
                base_checklist = checklist_a_ser_editado.original_checklist or checklist_a_ser_editado
                versao_mais_recente_anterior = Checklist.objects.filter(
                    Q(pk=base_checklist.pk) | Q(
                        original_checklist=base_checklist),
                    is_latest=True
                ).first()
                # --- FIM DA CORREÇÃO ---

                # 2. Cria a nova versão (a função interna agora calcula o número da versão corretamente).
                novo_checklist = _create_new_version_from_request(
                    request, checklist_a_ser_editado)

                # 3. Desativa a versão que ERA a mais recente, marcando-a como 'is_latest=False'.
                if versao_mais_recente_anterior:
                    versao_mais_recente_anterior.is_latest = False
                    versao_mais_recente_anterior.save()

                # 4. Encontra todos os Modelos de Auditoria que usavam a versão mais recente anterior.
                if versao_mais_recente_anterior:
                    modelos_afetados_ids = list(ModeloAuditoria.objects.filter(
                        checklist=versao_mais_recente_anterior
                    ).values_list('id', flat=True))

                    if modelos_afetados_ids:
                        # 5. Atualiza esses modelos para apontarem para o NOVO checklist.
                        ModeloAuditoria.objects.filter(
                            id__in=modelos_afetados_ids).update(checklist=novo_checklist)

                        # 6. Atualiza APENAS as instâncias de auditoria futuras.
                        AuditoriaInstancia.objects.filter(
                            auditoria_agendada__modelos__id__in=modelos_afetados_ids,
                            executada=False,
                            data_execucao__gt=timezone.now().date()
                        ).update(checklist_usado=novo_checklist)

                messages.success(
                    request, f'Checklist "{novo_checklist.nome}" atualizado para a versão {novo_checklist.version} com sucesso!')
                return redirect('auditorias:lista_checklists')

        except Exception as e:
            messages.error(request, f'Erro ao atualizar checklist: {repr(e)}')
            import traceback
            print(traceback.format_exc())

    # O contexto para o método GET (para exibir o formulário) continua o mesmo.
    context = {
        'checklist': checklist_a_ser_editado,
        'object': checklist_a_ser_editado,
        'ferramentas': FerramentaDigital.objects.all(),
        'status_opcoes': OpcaoResposta._meta.get_field('status').choices,
        'title': f'Editar Checklist: {checklist_a_ser_editado.nome} (V{checklist_a_ser_editado.version})',
        'back_url': 'auditorias:lista_checklists'
    }
    return render(request, 'auditorias/checklists/form.html', context)

# Supondo que seus models (AuditoriaInstancia, Checklist, SubSetor, Topico, etc.)
# estejam importados corretamente.
# from .models import AuditoriaInstancia, Checklist, SubSetor, Topico, Pergunta, OpcaoResposta, OpcaoPorcentagem


def _gerar_instancias_para_auditoria(auditoria, subsetores_selecionados_ids=None):
    """
    Função ATUALIZADA para gerar instâncias com base na nova lógica de agendamento.
    """
    # 1. Apaga todas as instâncias futuras que ainda não foram executadas
    auditoria.instancias.filter(
        executada=False,
        data_execucao__gte=timezone.now().date()
    ).delete()

    # 2. Busca o checklist mais recente a ser usado
    primeiro_modelo = auditoria.modelos.first()
    checklist_para_usar = None
    if primeiro_modelo and primeiro_modelo.checklist:
        checklist_base = primeiro_modelo.checklist
        original = checklist_base.original_checklist or checklist_base
        checklist_para_usar = Checklist.objects.filter(
            Q(pk=original.pk) | Q(original_checklist=original),
            is_latest=True
        ).first()

    # 3. Lógica para gerar a lista de datas
    dates_to_create = []
    if auditoria.data_inicio:
        current_date = auditoria.data_inicio
        end_date = auditoria.data_fim
        if not end_date:
            if not (auditoria.pular_finais_semana and current_date.weekday() >= 5):
                dates_to_create.append(current_date)
        else:
            loop_limit = 365 * 5
            loops = 0
            while current_date <= end_date and loops < loop_limit:
                loops += 1
                if not (auditoria.pular_finais_semana and current_date.weekday() >= 5):
                    dates_to_create.append(current_date)
                if auditoria.por_intervalo and auditoria.intervalo:
                    current_date += timedelta(days=auditoria.intervalo + 1)
                elif auditoria.por_frequencia and auditoria.frequencia:
                    # ... lógica de frequência ...
                    if auditoria.frequencia == 'DIARIO':
                        current_date += timedelta(days=1)
                    elif auditoria.frequencia == 'SEMANAL':
                        current_date += timedelta(weeks=1)
                    elif auditoria.frequencia == 'QUINZENAL':
                        current_date += timedelta(weeks=2)
                    elif auditoria.frequencia == 'MENSAL':
                        current_date += relativedelta(months=1)
                    elif auditoria.frequencia == 'ANUAL':
                        current_date += relativedelta(years=1)
                    else:
                        break
                else:
                    break

    # 4. Determina os locais e turnos
    target_locations = []

    if auditoria.agendamento_especifico:
        # CENÁRIO 2: Locais Específicos. Usa a lista de IDs recebida.
        if subsetores_selecionados_ids:
            target_locations = list(SubSetor.objects.filter(
                pk__in=subsetores_selecionados_ids))
    else:
        # CENÁRIO 1: Auditoria de Gestão ("Flutuante").
        # Se o nível NÃO for Subsetor, criamos uma instância sem local definido.
        if auditoria.nivel_organizacional != 'SUBSETOR':
            # O 'None' indica que o local será escolhido no app
            target_locations.append(None)
        elif auditoria.local_subsetor:
            # Caso especial: se o nível for Subsetor, o agendamento é para aquele local.
            target_locations.append(auditoria.local_subsetor)

    # Garante que não falhe se nenhuma localização for encontrada
    if not target_locations:
        target_locations.append(None)

    target_turnos = list(auditoria.turnos.all())
    if not target_turnos:
        target_turnos.append(None)

    repetitions = auditoria.numero_repeticoes if auditoria.numero_repeticoes and auditoria.numero_repeticoes > 0 else 1

    # 5. Cria as novas instâncias (lógica inalterada)
    instancias_a_criar = []
    for dt in dates_to_create:
        for location in target_locations:
            for turno in target_turnos:
                if turno and not turno.turnodetalhedia_set.filter(dia_semana=dt.weekday()).exists():
                    continue
                for _ in range(repetitions):
                    instancias_a_criar.append(AuditoriaInstancia(
                        auditoria_agendada=auditoria,
                        data_execucao=dt,
                        local_execucao=location,
                        responsavel=auditoria.responsavel,
                        turno=turno,
                        checklist_usado=checklist_para_usar
                    ))

    if instancias_a_criar:
        AuditoriaInstancia.objects.bulk_create(instancias_a_criar)


def processar_estrutura_checklist(request, checklist):
    """Processa e salva toda a estrutura de tópicos, perguntas e opções do checklist."""
    topicos_ids_processados = set()
    perguntas_ids_processadas = set()
    opcoes_resposta_ids_processadas = set()
    opcoes_porcentagem_ids_processadas = set()

    for key, value in request.POST.items():
        if key.startswith('topico-descricao['):
            topico_id_str = key.split('[')[1].split(']')[0]
            topico_descricao = value
            topico_ordem = request.POST.get(
                f'topico-ordem[{topico_id_str}]', 0)

            if topico_id_str.startswith('new-'):
                topico = Topico.objects.create(
                    checklist=checklist, descricao=topico_descricao, ordem=topico_ordem)
            else:
                topico = Topico.objects.get(
                    pk=int(topico_id_str), checklist=checklist)
                topico.descricao = topico_descricao
                topico.ordem = topico_ordem
                topico.save()
            topicos_ids_processados.add(topico.id)

            # Processar perguntas deste tópico
            for p_key, p_value in request.POST.items():
                if p_key.startswith(f'pergunta-descricao[{topico_id_str}-'):
                    pergunta_id_full = p_key.split('[')[1].split(']')[0]
                    pergunta_id_str = pergunta_id_full.replace(
                        f'{topico_id_str}-', '')

                    pergunta_descricao = p_value
                    pergunta_ordem = request.POST.get(
                        f'pergunta-ordem[{pergunta_id_full}]', 0)

                    if pergunta_id_str.startswith('new-'):
                        pergunta = Pergunta.objects.create(
                            topico=topico, descricao=pergunta_descricao, ordem=pergunta_ordem)
                    else:
                        pergunta = Pergunta.objects.get(
                            pk=int(pergunta_id_str), topico=topico)
                        pergunta.descricao = pergunta_descricao
                        pergunta.ordem = pergunta_ordem

                    pergunta.obrigatoria = request.POST.get(
                        f'pergunta-obrigatorio[{pergunta_id_full}]') == 'on'
                    pergunta.resposta_livre = request.POST.get(
                        f'pergunta-resposta_livre[{pergunta_id_full}]') == 'on'
                    pergunta.foto = request.POST.get(
                        f'pergunta-foto[{pergunta_id_full}]') == 'on'
                    pergunta.criar_opcao = request.POST.get(
                        f'pergunta-criar_opcao[{pergunta_id_full}]') == 'on'
                    pergunta.porcentagem = request.POST.get(
                        f'pergunta-porcentagem[{pergunta_id_full}]') == 'on'
                    pergunta.save()
                    perguntas_ids_processadas.add(pergunta.id)

                    # Processar opções de resposta
                    for o_key, o_value in request.POST.items():
                        if o_key.startswith(f'opcao-resposta-descricao[{pergunta_id_full}-'):
                            opcao_id_full = o_key.split('[')[1].split(']')[0]
                            opcao_id_str = opcao_id_full.replace(
                                f'{pergunta_id_full}-', '')

                            if opcao_id_str.startswith('new-'):
                                opcao = OpcaoResposta.objects.create(
                                    pergunta=pergunta)
                            else:
                                opcao = OpcaoResposta.objects.get(
                                    pk=int(opcao_id_str), pergunta=pergunta)

                            opcao.descricao = o_value
                            opcao.status = request.POST.get(
                                f'opcao-resposta-status[{opcao_id_full}]')
                            opcao.ordem = request.POST.get(
                                f'opcao-resposta-ordem[{opcao_id_full}]', 0)
                            opcao.save()
                            opcoes_resposta_ids_processadas.add(opcao.id)

                    # Processar opções de porcentagem
                    for o_key, o_value in request.POST.items():
                        if o_key.startswith(f'opcao-porcentagem-descricao[{pergunta_id_full}-'):
                            opcao_id_full = o_key.split('[')[1].split(']')[0]
                            opcao_id_str = opcao_id_full.replace(
                                f'{pergunta_id_full}-', '')

                            if opcao_id_str.startswith('new-'):
                                opcao = OpcaoPorcentagem.objects.create(
                                    pergunta=pergunta)
                            else:
                                opcao = OpcaoPorcentagem.objects.get(
                                    pk=int(opcao_id_str), pergunta=pergunta)

                            opcao.descricao = o_value
                            opcao.peso = request.POST.get(
                                f'opcao-porcentagem-peso[{opcao_id_full}]', 0)
                            opcao.cor = request.POST.get(
                                f'opcao-porcentagem-cor[{opcao_id_full}]', '#FFFFFF')
                            opcao.ordem = request.POST.get(
                                f'opcao-porcentagem-ordem[{opcao_id_full}]', 0)
                            opcao.save()
                            opcoes_porcentagem_ids_processadas.add(opcao.id)

    # Deletar itens que não foram processados (removidos do formulário)
    OpcaoResposta.objects.filter(pergunta__topico__checklist=checklist).exclude(
        id__in=opcoes_resposta_ids_processadas).delete()
    OpcaoPorcentagem.objects.filter(pergunta__topico__checklist=checklist).exclude(
        id__in=opcoes_porcentagem_ids_processadas).delete()
    Pergunta.objects.filter(topico__checklist=checklist).exclude(
        id__in=perguntas_ids_processadas).delete()
    Topico.objects.filter(checklist=checklist).exclude(
        id__in=topicos_ids_processados).delete()


@login_required
def deletar_checklist(request, pk):
    """Deleta um checklist"""
    checklist = get_object_or_404(Checklist, pk=pk)

    if request.method == 'POST':
        try:
            checklist.delete()
            messages.success(request, 'Checklist deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar checklist: {repr(e)}')
        return redirect('auditorias:lista_checklists')

    context = {
        'object': checklist,
        'title': 'Checklist'
    }
    return render(request, 'auditorias/deletar_generico.html', context)


@login_required
def historico_versoes_checklist(request, pk):
    """
    Lista todas as versões de um checklist específico.
    """
    checklist_atual = get_object_or_404(Checklist, pk=pk)

    # Encontra o checklist original (V1) para buscar todas as suas versões
    original = checklist_atual.original_checklist or checklist_atual

    # MODIFICAÇÃO: A consulta agora 'anota' (annotate) em cada versão
    # a contagem total de perguntas, somando as de todos os seus tópicos.
    versoes = Checklist.objects.filter(
        Q(pk=original.pk) | Q(original_checklist=original)
    ).prefetch_related(
        'topicos'
    ).annotate(
        total_perguntas=Count('topicos__perguntas')
    ).order_by('-version')

    context = {
        'versoes': versoes,
        'original': original,
        'title': f'Histórico de Versões - {original.nome}',
    }

    return render(request, 'auditorias/checklists/historico.html', context)


@login_required
def comparar_versoes_checklist(request, pk):
    """
    View para comparar múltiplas versões de um checklist.
    Permite selecionar e comparar 2 ou mais versões lado a lado.
    """
    checklist_atual = get_object_or_404(Checklist, pk=pk)

    # Encontra o checklist original
    original = checklist_atual.original_checklist or checklist_atual

    # Busca todas as versões
    versoes = (Checklist.objects.filter(
        Q(pk=original.pk) | Q(original_checklist=original)
    ).prefetch_related(
        'topicos__perguntas__opcoes_resposta',
        'topicos__perguntas__opcoes_porcentagem'
    ).order_by('-version'))

    # Se versões específicas foram selecionadas para comparação
    versoes_selecionadas_ids = request.GET.getlist('versoes')

    if versoes_selecionadas_ids and len(versoes_selecionadas_ids) >= 2:
        versoes_para_comparar = versoes.filter(
            pk__in=versoes_selecionadas_ids
        ).order_by('version')

        # Gera dados de comparação
        comparacao_data = _gerar_dados_comparacao(versoes_para_comparar)

        context = {
            'original': original,
            'versoes': versoes,
            'versoes_comparadas': versoes_para_comparar,
            'comparacao_data': comparacao_data,
            'title': f'Comparar Versões - {original.nome}',
        }
    else:
        context = {
            'original': original,
            'versoes': versoes,
            'versoes_comparadas': None,
            'title': f'Selecionar Versões para Comparar - {original.nome}',
        }

    return render(request, 'auditorias/checklists/comparar_versoes.html', context)


def _gerar_dados_comparacao(versoes):
    """
    Gera estrutura de dados para comparação entre versões.
    Retorna um dicionário com as diferenças detectadas organizadas para exibição lado a lado.
    """
    comparacao = {
        'versoes_info': [],
        'topicos_comparados': [],
        'alteracoes_resumo': {
            'topicos_adicionados': 0,
            'topicos_removidos': 0,
            'perguntas_adicionadas': 0,
            'perguntas_removidas': 0,
            'perguntas_modificadas': 0,
        }
    }

    # Informações básicas de cada versão
    versoes_list = list(versoes)
    for v in versoes_list:
        comparacao['versoes_info'].append({
            'id': v.pk,
            'version': v.version,
            'nome': v.nome,
            'data': v.data_cadastro,
            'total_topicos': v.topicos.count(),
            'total_perguntas': sum(t.perguntas.count() for t in v.topicos.all()),
        })

    # Criar estrutura de dados para cada versão
    versoes_data = {}
    for v in versoes_list:
        versoes_data[v.pk] = {}
        for topico in v.topicos.all():
            if topico.descricao not in versoes_data[v.pk]:
                versoes_data[v.pk][topico.descricao] = []

            for pergunta in topico.perguntas.all():
                versoes_data[v.pk][topico.descricao].append({
                    'id': pergunta.pk,
                    'descricao': pergunta.descricao,
                    'ordem': pergunta.ordem,
                    'obrigatoria': pergunta.obrigatoria,
                    'resposta_livre': pergunta.resposta_livre,
                    'foto': pergunta.foto,
                    'criar_opcao': pergunta.criar_opcao,
                    'porcentagem': pergunta.porcentagem,
                    'opcoes_resposta': [
                        {'descricao': o.descricao, 'status': o.status,
                            'status_display': o.get_status_display()}
                        for o in pergunta.opcoes_resposta.all()
                    ],
                    'opcoes_porcentagem': [
                        {'descricao': o.descricao, 'peso': o.peso}
                        for o in pergunta.opcoes_porcentagem.all()
                    ],
                })

    # Obter todos os tópicos únicos
    todos_topicos = set()
    for v_pk in versoes_data:
        todos_topicos.update(versoes_data[v_pk].keys())

    # Análise de alterações entre primeira e última versão
    if len(versoes_list) >= 2:
        primeira_versao = versoes_list[0]
        ultima_versao = versoes_list[-1]

        topicos_primeira = set(versoes_data[primeira_versao.pk].keys())
        topicos_ultima = set(versoes_data[ultima_versao.pk].keys())

        comparacao['alteracoes_resumo']['topicos_adicionados'] = len(
            topicos_ultima - topicos_primeira)
        comparacao['alteracoes_resumo']['topicos_removidos'] = len(
            topicos_primeira - topicos_ultima)

        # Contar perguntas
        for topico in topicos_primeira & topicos_ultima:
            pergs_primeira = versoes_data[primeira_versao.pk][topico]
            pergs_ultima = versoes_data[ultima_versao.pk][topico]

            desc_primeira = [p['descricao'] for p in pergs_primeira]
            desc_ultima = [p['descricao'] for p in pergs_ultima]

            comparacao['alteracoes_resumo']['perguntas_adicionadas'] += len(
                set(desc_ultima) - set(desc_primeira))
            comparacao['alteracoes_resumo']['perguntas_removidas'] += len(
                set(desc_primeira) - set(desc_ultima))

            # Contar modificadas
            for p1 in pergs_primeira:
                for p2 in pergs_ultima:
                    if p1['descricao'] == p2['descricao']:
                        # Verifica se outras propriedades mudaram
                        if (p1['obrigatoria'] != p2['obrigatoria'] or
                            p1['resposta_livre'] != p2['resposta_livre'] or
                            p1['foto'] != p2['foto'] or
                            p1['criar_opcao'] != p2['criar_opcao'] or
                            p1['porcentagem'] != p2['porcentagem'] or
                            p1['opcoes_resposta'] != p2['opcoes_resposta'] or
                                p1['opcoes_porcentagem'] != p2['opcoes_porcentagem']):
                            comparacao['alteracoes_resumo']['perguntas_modificadas'] += 1
                        break

    # Organizar dados para exibição lado a lado
    for topico_nome in sorted(todos_topicos):
        topico_data = {
            'nome': topico_nome,
            'perguntas_agrupadas': []
        }

        # Coletar todas as perguntas únicas deste tópico de todas as versões
        todas_perguntas_desc = set()
        for v_pk in versoes_data:
            if topico_nome in versoes_data[v_pk]:
                for p in versoes_data[v_pk][topico_nome]:
                    todas_perguntas_desc.add(p['descricao'])

        # Para cada descrição de pergunta única, criar uma linha de comparação
        for pergunta_desc in sorted(todas_perguntas_desc):
            linha_pergunta = {
                'descricao': pergunta_desc,
                'versoes_dados': {}
            }

            # Para cada versão, buscar a pergunta com essa descrição
            for v in versoes_list:
                v_pk = v.pk
                linha_pergunta['versoes_dados'][v_pk] = None

                if topico_nome in versoes_data[v_pk]:
                    for p in versoes_data[v_pk][topico_nome]:
                        if p['descricao'] == pergunta_desc:
                            linha_pergunta['versoes_dados'][v_pk] = p
                            break

            topico_data['perguntas_agrupadas'].append(linha_pergunta)

        comparacao['topicos_comparados'].append(topico_data)

    return comparacao


@login_required
def exportar_checklists_csv(request):
    response = HttpResponse(
        content_type='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': 'attachment; filename="checklists.csv"'}
    )

    writer = csv.writer(response)
    writer.writerow(['Nome', 'Ferramenta', 'Status'])

    search = request.GET.get('search', '')
    checklists = Checklist.objects.select_related('ferramenta').all()
    if search:
        checklists = checklists.filter(nome__icontains=search)

    for checklist in checklists:
        writer.writerow([
            checklist.nome,
            checklist.ferramenta.nome if checklist.ferramenta else 'N/A',
            'Ativo' if checklist.ativo else 'Inativo'
        ])

    return response

# ============================================================================
# VIEWS PARA MODELOS DE AUDITORIA
# ============================================================================


@login_required
def lista_modelos_auditoria(request):
    """Lista todos os modelos de auditoria"""
    search = request.GET.get('search', '')
    modelos = ModeloAuditoria.objects.select_related(
        'checklist', 'categoria', 'ferramenta_causa_raiz').all()

    if search:
        modelos = modelos.filter(descricao__icontains=search)

    paginator = Paginator(modelos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Modelos de Auditoria',
        'singular': 'Modelo de Auditoria',
        'button_text': 'Novo Modelo de Auditoria',
        'create_url': 'auditorias:criar_modelo_auditoria',
        'export_url': 'auditorias:exportar_modelos_auditoria_csv',  # NOVO
        'artigo': 'o',
        'empty_message': 'Nenhum modelo de auditoria cadastrado',
        'empty_subtitle': 'Comece criando o primeiro modelo de auditoria.'
    }
    return render(request, 'auditorias/modelos_auditoria/lista.html', context)


@login_required
def criar_modelo_auditoria(request):
    """Cria um novo modelo de auditoria"""
    if request.method == 'POST':
        descricao = request.POST.get('descricao')
        ativo = request.POST.get('ativo') == 'on'
        iniciar_por_codigo_qr = request.POST.get(
            'iniciar_por_codigo_qr') == 'on'
        checklist_id = request.POST.get('checklist')
        categoria_id = request.POST.get('categoria')
        ferramenta_causa_raiz_id = request.POST.get('ferramenta_causa_raiz')

        if descricao:
            try:
                modelo = ModeloAuditoria.objects.create(
                    descricao=descricao,
                    ativo=ativo,
                    iniciar_por_codigo_qr=iniciar_por_codigo_qr
                )

                if checklist_id:
                    modelo.checklist = Checklist.objects.get(pk=checklist_id)
                if categoria_id:
                    modelo.categoria = CategoriaAuditoria.objects.get(
                        pk=categoria_id)
                if ferramenta_causa_raiz_id:
                    modelo.ferramenta_causa_raiz = FerramentaCausaRaiz.objects.get(
                        pk=ferramenta_causa_raiz_id)

                modelo.save()
                messages.success(
                    request, 'Modelo de auditoria criado com sucesso!')
                return redirect('auditorias:lista_modelos_auditoria')
            except Exception as e:
                messages.error(request, f'Erro ao criar modelo: {repr(e)}')
        else:
            messages.error(request, 'Descrição é obrigatória!')

    context = {
        'checklists': Checklist.objects.filter(ativo=True),
        'categorias': CategoriaAuditoria.objects.filter(ativo=True),
        'ferramentas_causa_raiz': FerramentaCausaRaiz.objects.all(),
        'title': 'Criar Modelo de Auditoria',
        'back_url': 'auditorias:lista_modelos_auditoria'
    }
    return render(request, 'auditorias/modelos_auditoria/form.html', context)


@login_required
def editar_modelo_auditoria(request, pk):
    """Edita um modelo de auditoria existente"""
    modelo = get_object_or_404(ModeloAuditoria, pk=pk)

    if request.method == 'POST':
        modelo.descricao = request.POST.get('descricao')
        modelo.ativo = request.POST.get('ativo') == 'on'
        modelo.iniciar_por_codigo_qr = request.POST.get(
            'iniciar_por_codigo_qr') == 'on'

        checklist_id = request.POST.get('checklist')
        categoria_id = request.POST.get('categoria')
        ferramenta_causa_raiz_id = request.POST.get('ferramenta_causa_raiz')

        if checklist_id:
            modelo.checklist = Checklist.objects.get(pk=checklist_id)
        else:
            modelo.checklist = None

        if categoria_id:
            modelo.categoria = CategoriaAuditoria.objects.get(pk=categoria_id)
        else:
            modelo.categoria = None

        if ferramenta_causa_raiz_id:
            modelo.ferramenta_causa_raiz = FerramentaCausaRaiz.objects.get(
                pk=ferramenta_causa_raiz_id)
        else:
            modelo.ferramenta_causa_raiz = None

        try:
            modelo.save()
            messages.success(
                request, 'Modelo de auditoria atualizado com sucesso!')
            return redirect('auditorias:lista_modelos_auditoria')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar modelo: {repr(e)}')

    context = {
        'modelo': modelo,
        'checklists': Checklist.objects.filter(ativo=True),
        'categorias': CategoriaAuditoria.objects.filter(ativo=True),
        'ferramentas_causa_raiz': FerramentaCausaRaiz.objects.all(),
        'title': 'Editar Modelo de Auditoria',
        'back_url': 'auditorias:lista_modelos_auditoria'
    }
    return render(request, 'auditorias/modelos_auditoria/form.html', context)


@login_required
def deletar_modelo_auditoria(request, pk):
    """Deleta um modelo de auditoria"""
    modelo = get_object_or_404(ModeloAuditoria, pk=pk)

    if request.method == 'POST':
        try:
            modelo.delete()
            messages.success(
                request, 'Modelo de auditoria deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar modelo: {repr(e)}')
        return redirect('auditorias:lista_modelos_auditoria')

    context = {
        'object': modelo,
        'title': 'Modelo de Auditoria'
    }
    return render(request, 'auditorias/deletar_generico.html', context)


@login_required
def exportar_modelos_auditoria_csv(request):

    response = HttpResponse(
        content_type='text/csv; charset=utf-8-sig',
        headers={
            'Content-Disposition': 'attachment; filename="modelos_auditoria.csv"'}
    )

    writer = csv.writer(response)
    writer.writerow(['Descrição', 'Checklist', 'Categoria', 'Status'])

    search = request.GET.get('search', '')
    modelos = ModeloAuditoria.objects.select_related(
        'checklist', 'categoria').all()
    if search:
        modelos = modelos.filter(descricao__icontains=search)

    for modelo in modelos:
        writer.writerow([
            modelo.descricao,
            modelo.checklist.nome if modelo.checklist else 'N/A',
            modelo.categoria.descricao if modelo.categoria else 'N/A',
            'Ativo' if modelo.ativo else 'Inativo'
        ])

    return response

# ============================================================================
# VIEWS PARA AUDITORIAS
# ============================================================================


@login_required
def lista_auditorias(request):
    """Lista todas as auditorias agendadas"""
    search = request.GET.get('search', '')
    auditorias = Auditoria.objects.select_related(
        'responsavel',
        'ferramenta',
        'criado_por'
    ).prefetch_related(
        'modelos'
    ).all()

    if search:
        auditorias = auditorias.filter(
            Q(responsavel__first_name__icontains=search) |
            Q(responsavel__last_name__icontains=search) |
            Q(ferramenta__nome__icontains=search)
        )

    paginator = Paginator(auditorias, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # --- INÍCIO DA CORREÇÃO ---
    all_users_list = list(Usuario.objects.filter(is_active=True).annotate(
        name=Concat('first_name', Value(' '), 'last_name')
    ).values('id', 'name'))
    # --- FIM DA CORREÇÃO ---

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Agendamento de Auditorias',
        'singular': 'Auditoria',
        'button_text': 'Criar Auditoria',
        'create_url': 'auditorias:criar_auditoria',
        'artigo': 'a',
        'empty_message': 'Nenhuma auditoria agendada',
        'empty_subtitle': 'Comece criando a primeira auditoria.',
        # Passa o JSON para o template
        'all_users_json': json.dumps(all_users_list)
    }
    return render(request, 'auditorias/auditorias/lista.html', context)


@login_required
def criar_auditoria(request):
    """Cria uma nova auditoria agendada com a nova lógica de locais."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # --- Captura todos os dados do formulário ---
                data_inicio_str = request.POST.get('data_inicio')
                data_fim_str = request.POST.get('data_fim')
                data_inicio = datetime.strptime(
                    data_inicio_str, '%Y-%m-%d').date()
                data_fim = datetime.strptime(
                    data_fim_str, '%Y-%m-%d').date() if data_fim_str else None

                schedule_type = request.POST.get('schedule_type')

                # --- NOVA LÓGICA DE AGENDAMENTO ---
                agendamento_especifico = request.POST.get(
                    'agendamento_especifico') == 'on'
                subsetores_selecionados_ids = request.POST.getlist(
                    'subsetores_selecionados')

                auditoria = Auditoria(
                    criado_por=request.user,
                    ferramenta_id=request.POST.get('ferramenta'),
                    responsavel_id=request.POST.get('responsavel'),
                    nivel_organizacional=request.POST.get(
                        'nivel_organizacional'),
                    categoria_auditoria=request.POST.get(
                        'categoria_auditoria'),
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    local_empresa_id=request.POST.get('local_empresa') or None,
                    local_area_id=request.POST.get('local_area') or None,
                    local_setor_id=request.POST.get('local_setor') or None,
                    local_subsetor_id=request.POST.get(
                        'local_subsetor') or None,
                    por_frequencia=schedule_type == 'por_frequencia',
                    por_intervalo=schedule_type == 'por_intervalo',
                    frequencia=request.POST.get('frequencia') or None,
                    intervalo=int(request.POST.get('intervalo')
                                  ) if request.POST.get('intervalo') else None,
                    numero_repeticoes=int(request.POST.get('numero_repeticoes')) if request.POST.get(
                        'numero_repeticoes') else None,
                    pular_finais_semana=request.POST.get(
                        'pular_finais_semana') == 'on',
                    contem_turnos=request.POST.get('contem_turnos') == 'on',
                    agendamento_especifico=agendamento_especifico  # Salva o novo flag
                )
                auditoria.save()

                auditoria.modelos.set(request.POST.getlist('modelos'))
                auditoria.ativos_auditados.set(
                    request.POST.getlist('ativos_auditados'))
                auditoria.turnos.set(request.POST.getlist('turnos'))

                # --- CHAMA A FUNÇÃO ATUALIZADA ---
                _gerar_instancias_para_auditoria(
                    auditoria, subsetores_selecionados_ids)

            messages.success(request, 'Auditoria criada com sucesso!')
            return redirect('auditorias:lista_auditorias')
        except Exception as e:
            messages.error(request, f'Erro ao criar auditoria: {repr(e)}')
            import traceback
            traceback.print_exc()  # Para debug no terminal

    # Contexto para o método GET
    context = {
        'ferramentas': FerramentaDigital.objects.all(),
        'usuarios': Usuario.objects.filter(is_active=True),
        'empresas': Empresa.objects.filter(ativo=True),
        'areas': Area.objects.filter(ativo=True),
        'setores': Setor.objects.filter(ativo=True),
        'subsetores': SubSetor.objects.filter(ativo=True),
        'modelos': ModeloAuditoria.objects.filter(ativo=True),
        'ativos': Ativo.objects.filter(ativo=True),
        'turnos': Turno.objects.filter(ativo=True),
        'title': 'Criar Auditoria',
        'back_url': 'auditorias:lista_auditorias'
    }
    return render(request, 'auditorias/auditorias/form.html', context)


@login_required
def editar_auditoria(request, pk):
    """Edita uma auditoria existente com a nova lógica de locais."""
    auditoria = get_object_or_404(Auditoria, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                data_inicio_str = request.POST.get('data_inicio')
                data_fim_str = request.POST.get('data_fim')
                auditoria.data_inicio = datetime.strptime(
                    data_inicio_str, '%Y-%m-%d').date()
                auditoria.data_fim = datetime.strptime(
                    data_fim_str, '%Y-%m-%d').date() if data_fim_str else None

                schedule_type = request.POST.get('schedule_type')

                # --- NOVA LÓGICA DE AGENDAMENTO ---
                agendamento_especifico = request.POST.get(
                    'agendamento_especifico') == 'on'
                subsetores_selecionados_ids = request.POST.getlist(
                    'subsetores_selecionados')

                auditoria.ferramenta_id = request.POST.get('ferramenta')
                auditoria.responsavel_id = request.POST.get('responsavel')
                auditoria.nivel_organizacional = request.POST.get(
                    'nivel_organizacional')
                auditoria.categoria_auditoria = request.POST.get(
                    'categoria_auditoria')
                auditoria.local_empresa_id = request.POST.get(
                    'local_empresa') or None
                auditoria.local_area_id = request.POST.get(
                    'local_area') or None
                auditoria.local_setor_id = request.POST.get(
                    'local_setor') or None
                auditoria.local_subsetor_id = request.POST.get(
                    'local_subsetor') or None
                auditoria.por_frequencia = schedule_type == 'por_frequencia'
                auditoria.por_intervalo = schedule_type == 'por_intervalo'
                auditoria.frequencia = request.POST.get('frequencia') or None
                auditoria.intervalo = int(request.POST.get(
                    'intervalo')) if request.POST.get('intervalo') else None
                auditoria.numero_repeticoes = int(request.POST.get(
                    'numero_repeticoes')) if request.POST.get('numero_repeticoes') else None
                auditoria.pular_finais_semana = request.POST.get(
                    'pular_finais_semana') == 'on'
                auditoria.contem_turnos = request.POST.get(
                    'contem_turnos') == 'on'
                auditoria.agendamento_especifico = agendamento_especifico  # Salva o novo flag

                auditoria.save()

                auditoria.modelos.set(request.POST.getlist('modelos'))
                auditoria.ativos_auditados.set(
                    request.POST.getlist('ativos_auditados'))
                auditoria.turnos.set(request.POST.getlist('turnos'))

                # --- CHAMA A FUNÇÃO ATUALIZADA ---
                _gerar_instancias_para_auditoria(
                    auditoria, subsetores_selecionados_ids)

            messages.success(request, 'Auditoria atualizada com sucesso!')
            return redirect('auditorias:lista_auditorias')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar auditoria: {repr(e)}')
            import traceback
            traceback.print_exc()  # Para debug

    # Contexto para o método GET
    context = {
        'auditoria': auditoria,
        'ferramentas': FerramentaDigital.objects.all(),
        'usuarios': Usuario.objects.filter(is_active=True),
        'empresas': Empresa.objects.filter(ativo=True),
        'areas': Area.objects.filter(ativo=True),
        'setores': Setor.objects.filter(ativo=True),
        'subsetores': SubSetor.objects.filter(ativo=True),
        'modelos': ModeloAuditoria.objects.filter(ativo=True),
        'ativos': Ativo.objects.filter(ativo=True),
        'turnos': Turno.objects.filter(ativo=True),
        'title': 'Editar Auditoria',
        'back_url': 'auditorias:lista_auditorias'
    }
    return render(request, 'auditorias/auditorias/form.html', context)


@login_required
def deletar_auditoria(request, pk):
    """Deleta uma auditoria"""
    auditoria = get_object_or_404(Auditoria, pk=pk)

    if request.method == 'POST':
        try:
            auditoria.delete()
            messages.success(request, 'Auditoria deletada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar auditoria: {repr(e)}')
        return redirect('auditorias:lista_auditorias')

    context = {
        'object': auditoria,
        'title': 'Auditoria'
    }
    return render(request, 'auditorias/deletar_generico.html', context)


# ============================================================================
# VIEWS AJAX PARA FILTROS DINÂMICOS
# ============================================================================

@login_required
def get_areas_por_empresa(request):
    """Retorna áreas de uma empresa via AJAX"""
    empresa_id = request.GET.get('empresa_id')
    areas = Area.objects.filter(
        empresa_id=empresa_id, ativo=True).values('id', 'nome')
    return JsonResponse(list(areas), safe=False)


@login_required
def get_setores_por_area(request):
    """Retorna setores de uma área via AJAX"""
    area_id = request.GET.get('area_id')
    setores = Setor.objects.filter(
        area_id=area_id, ativo=True).values('id', 'nome')
    return JsonResponse(list(setores), safe=False)


@login_required
def get_subsetores_por_setor(request):
    """Retorna subsetores de um setor via AJAX"""
    setor_id = request.GET.get('setor_id')
    subsetores = SubSetor.objects.filter(
        setor_id=setor_id, ativo=True).values('id', 'nome')
    return JsonResponse(list(subsetores), safe=False)


@login_required
def get_ativos_por_local(request):
    """Retorna ativos filtrados por localização via AJAX"""
    nivel = request.GET.get('nivel')
    local_id = request.GET.get('local_id')

    ativos = Ativo.objects.filter(ativo=True)

    if nivel == 'EMPRESA' and local_id:
        ativos = ativos.filter(
            estrutura_organizacional__setor__area__empresa_id=local_id)
    elif nivel == 'AREA' and local_id:
        ativos = ativos.filter(
            estrutura_organizacional__setor__area_id=local_id)
    elif nivel == 'SETOR' and local_id:
        ativos = ativos.filter(estrutura_organizacional__setor_id=local_id)
    elif nivel == 'SUBSETOR' and local_id:
        ativos = ativos.filter(estrutura_organizacional_id=local_id)

    ativos_data = ativos.values('id', 'tag', 'descricao')
    return JsonResponse(list(ativos_data), safe=False)

# --- ADICIONE ESTA NOVA VIEW ABAIXO ---


@login_required
def get_subsetores_por_nivel(request):
    """
    Retorna subsetores filtrados por nível organizacional (Empresa, Área, ou Setor).
    """
    empresa_id = request.GET.get('empresa_id')
    area_id = request.GET.get('area_id')
    setor_id = request.GET.get('setor_id')

    queryset = SubSetor.objects.filter(ativo=True)

    if setor_id:
        queryset = queryset.filter(setor_id=setor_id)
    elif area_id:
        queryset = queryset.filter(setor__area_id=area_id)
    elif empresa_id:
        queryset = queryset.filter(setor__area__empresa_id=empresa_id)
    else:
        # Se nenhum ID for fornecido, retorna uma lista vazia
        queryset = queryset.none()

    subsetores = queryset.values('id', 'nome').order_by('nome')
    return JsonResponse(list(subsetores), safe=False)
# --- FIM DA NOVA VIEW ---


@login_required
def lista_perguntas(request, checklist_pk):
    """Lista todas as perguntas de um checklist, agrupadas por tópico."""
    checklist = get_object_or_404(Checklist, pk=checklist_pk)
    topicos_com_perguntas = checklist.topicos.prefetch_related(
        'perguntas').order_by('ordem')

    context = {
        'checklist': checklist,
        'topicos_com_perguntas': topicos_com_perguntas,
        'title': f'Perguntas do Checklist: {checklist.nome}',
        'back_url': 'auditorias:lista_checklists'
    }
    return render(request, 'auditorias/perguntas/lista.html', context)


@login_required
def criar_pergunta(request, checklist_pk):
    """Cria uma nova pergunta para um tópico dentro de um checklist."""
    checklist = get_object_or_404(Checklist, pk=checklist_pk)

    if request.method == 'POST':
        topico_id = request.POST.get('topico')
        descricao = request.POST.get('descricao')

        if topico_id and descricao:
            try:
                Pergunta.objects.create(
                    topico_id=topico_id,
                    descricao=descricao,
                    campo_obrigatorio=request.POST.get(
                        'campo_obrigatorio') == 'on',
                    campo_desabilitado=request.POST.get(
                        'campo_desabilitado') == 'on',
                    ordem=int(request.POST.get('ordem', 0))
                )
                messages.success(request, 'Pergunta criada com sucesso!')
                return redirect('auditorias:lista_perguntas', checklist_pk=checklist.pk)
            except Exception as e:
                messages.error(request, f'Erro ao criar pergunta: {e}')
        else:
            messages.error(request, 'Tópico e Descrição são obrigatórios.')

    context = {
        'checklist': checklist,
        'topicos': checklist.topicos.order_by('ordem'),
        'title': 'Criar Nova Pergunta',
        'back_url': reverse('auditorias:lista_perguntas', kwargs={'checklist_pk': checklist.pk}),
    }
    return render(request, 'auditorias/perguntas/form.html', context)


@login_required
def editar_pergunta(request, pk):
    """Edita uma pergunta existente."""
    pergunta = get_object_or_404(Pergunta.objects.select_related(
        'topico__checklist').prefetch_related('opcoes_resposta', 'opcoes_porcentagem'), pk=pk)
    checklist = pergunta.topico.checklist

    if request.method == 'POST':
        topico_id = request.POST.get('topico')
        descricao = request.POST.get('descricao')

        if topico_id and descricao:
            try:
                pergunta.topico_id = topico_id
                pergunta.descricao = descricao
                pergunta.campo_obrigatorio = request.POST.get(
                    'campo_obrigatorio') == 'on'
                pergunta.campo_desabilitado = request.POST.get(
                    'campo_desabilitado') == 'on'
                pergunta.ordem = int(request.POST.get('ordem', 0))
                pergunta.save()

                messages.success(request, 'Pergunta atualizada com sucesso!')
                return redirect('auditorias:lista_perguntas', checklist_pk=checklist.pk)
            except Exception as e:
                messages.error(request, f'Erro ao atualizar pergunta: {e}')
        else:
            messages.error(request, 'Tópico e Descrição são obrigatórios.')

    context = {
        'object': pergunta,
        'checklist': checklist,
        'topicos': checklist.topicos.order_by('ordem'),
        'title': 'Editar Pergunta',
        'back_url': reverse('auditorias:lista_perguntas', kwargs={'checklist_pk': checklist.pk}),
    }
    return render(request, 'auditorias/perguntas/form.html', context)


@login_required
def deletar_pergunta(request, pk):
    """Deleta uma pergunta."""
    pergunta = get_object_or_404(
        Pergunta.objects.select_related('topico__checklist'), pk=pk)
    checklist_pk = pergunta.topico.checklist.pk

    if request.method == 'POST':
        try:
            pergunta.delete()
            messages.success(request, 'Pergunta deletada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar pergunta: {e}')
        return redirect('auditorias:lista_perguntas', checklist_pk=checklist_pk)

    context = {
        'object': pergunta,
        'title': 'Pergunta',
        'back_url': reverse('auditorias:lista_perguntas', kwargs={'checklist_pk': checklist_pk}),
    }
    return render(request, 'auditorias/deletar_pergunta.html', context)


@login_required
def lista_topicos(request):
    """Lista todos os tópicos com busca e paginação."""
    search = request.GET.get('search', '')
    topicos = Topico.objects.select_related(
        'checklist').order_by('checklist__nome', 'ordem')

    if search:
        topicos = topicos.filter(
            Q(descricao__icontains=search) | Q(
                checklist__nome__icontains=search)
        )

    paginator = Paginator(topicos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Tópicos de Checklist',
        'singular': 'Tópico',
        'button_text': 'Novo Tópico',
        'create_url': 'auditorias:criar_topico',
        'artigo': 'o',
        'empty_message': 'Nenhum tópico cadastrado.',
        'empty_subtitle': 'Comece criando o primeiro tópico.'
    }
    return render(request, 'auditorias/topicos/lista.html', context)


@login_required
def criar_topico(request):
    """Cria um novo tópico."""
    if request.method == 'POST':
        descricao = request.POST.get('descricao')
        checklist_id = request.POST.get('checklist')
        ordem = request.POST.get('ordem', 0)

        if descricao and checklist_id:
            try:
                Topico.objects.create(
                    descricao=descricao,
                    checklist_id=checklist_id,
                    ordem=int(ordem)
                )
                messages.success(request, 'Tópico criado com sucesso!')
                return redirect('auditorias:lista_topicos')
            except Exception as e:
                messages.error(request, f'Erro ao criar tópico: {e}')
        else:
            messages.error(request, 'Descrição e Checklist são obrigatórios.')

    context = {
        'title': 'Criar Tópico',
        'back_url': 'auditorias:lista_topicos',
        'checklists': Checklist.objects.filter(ativo=True)
    }
    return render(request, 'auditorias/topicos/form.html', context)


@login_required
def editar_topico(request, pk):
    """Edita um tópico existente."""
    topico = get_object_or_404(Topico, pk=pk)
    if request.method == 'POST':
        topico.descricao = request.POST.get('descricao')
        topico.checklist_id = request.POST.get('checklist')
        topico.ordem = int(request.POST.get('ordem', 0))

        if topico.descricao and topico.checklist_id:
            try:
                topico.save()
                messages.success(request, 'Tópico atualizado com sucesso!')
                return redirect('auditorias:lista_topicos')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar tópico: {e}')
        else:
            messages.error(request, 'Descrição e Checklist são obrigatórios.')

    context = {
        'object': topico,
        'title': 'Editar Tópico',
        'back_url': 'auditorias:lista_topicos',
        'checklists': Checklist.objects.filter(ativo=True)
    }
    return render(request, 'auditorias/topicos/form.html', context)


@login_required
def deletar_topico(request, pk):
    """Deleta um tópico."""
    topico = get_object_or_404(Topico, pk=pk)
    if request.method == 'POST':
        try:
            topico.delete()
            messages.success(request, 'Tópico deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar tópico: {e}')
        return redirect('auditorias:lista_topicos')

    context = {
        'object': topico,
        'title': 'Tópico'
    }
    return render(request, 'auditorias/deletar_generico.html', context)


class AuditoriasPendentesAPIView(ListAPIView):
    """
    Endpoint da API que retorna a lista de instâncias de auditoria
    pendentes para o usuário autenticado.
    """
    serializer_class = AuditoriaInstanciaListSerializer
    # Garante que apenas usuários logados acessem
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Este método é sobrescrito para retornar apenas os objetos
        relevantes para o usuário que fez a requisição.
        """
        user = self.request.user
        # Filtra as instâncias não executadas
        # E que a auditoria pai tenha o usuário logado como responsável
        return AuditoriaInstancia.objects.filter(
            executada=False,
            responsavel=user,
            # Filtra para incluir apenas auditorias de hoje ou do passado
            data_execucao__lte=timezone.now().date()
        ).select_related(
            'auditoria_agendada__local_empresa',
            'auditoria_agendada__local_area',
            'auditoria_agendada__local_setor',
            'auditoria_agendada__local_subsetor',
            'auditoria_agendada__ferramenta'
        ).order_by('data_execucao')


class AuditoriaInstanciaDetailAPIView(RetrieveAPIView):
    """
    Endpoint da API que retorna os detalhes completos de uma
    única instância de auditoria, incluindo o checklist.
    """
    serializer_class = AuditoriaInstanciaDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Garante que o usuário só possa ver instâncias de auditorias
        pelas quais ele é o responsável.
        """
        user = self.request.user
        return AuditoriaInstancia.objects.filter(responsavel=user)


class SubmeterAuditoriaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            instancia = AuditoriaInstancia.objects.get(
                pk=pk,
                responsavel=request.user,
                executada=False
            )
        except AuditoriaInstancia.DoesNotExist:
            return Response(
                {"detail": "Instância de auditoria não encontrada ou já finalizada."},
                status=status.HTTP_404_NOT_FOUND
            )

        # --- NOVA LÓGICA PARA ATUALIZAR O LOCAL ---
        local_execucao_id = request.data.get('local_execucao_id')
        if local_execucao_id and instancia.local_execucao is None:
            try:
                subsetor = SubSetor.objects.get(pk=local_execucao_id)
                instancia.local_execucao = subsetor
                # Não salvamos ainda, vamos salvar junto com o 'executada=True'
            except SubSetor.DoesNotExist:
                return Response(
                    {"detail": "O local de execução (subsetor) fornecido não é válido."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        # --- FIM DA NOVA LÓGICA ---

        respostas_data = request.data.get('respostas', [])
        contexto = {'auditoria_instancia': instancia}
        respostas_serializer = RespostaSerializer(
            data=respostas_data, many=True, context=contexto)

        if respostas_serializer.is_valid():
            respostas_serializer.save()

            instancia.executada = True
            instancia.save()  # Agora salva o 'local_execucao' atualizado e o 'executada'

            return Response(
                {"detail": "Auditoria submetida com sucesso!"},
                status=status.HTTP_200_OK
            )

        return Response(respostas_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LocaisPermitidosAPIView(ListAPIView):
    """
    Endpoint da API que retorna a lista de SubSetores permitidos
    para uma instância de auditoria de gestão (flutuante).
    """
    permission_classes = [IsAuthenticated]

    def get_serializer(self, *args, **kwargs):
        # Esta view não usa um serializer padrão, então retornamos None
        return None

    def get_queryset(self):
        """
        Filtra os subsetores com base no Nível Organizacional
        definido no Agendamento "pai" da instância.
        """
        instancia_id = self.kwargs.get('pk')
        try:
            instancia = AuditoriaInstancia.objects.select_related(
                'auditoria_agendada'
            ).get(pk=instancia_id, responsavel=self.request.user)
        except AuditoriaInstancia.DoesNotExist:
            return SubSetor.objects.none()  # Retorna vazio se não encontrar

        agendamento = instancia.auditoria_agendada
        nivel = agendamento.nivel_organizacional

        # Se for auditoria de gestão, busca os locais permitidos
        if not instancia.local_execucao and not agendamento.agendamento_especifico:
            if nivel == 'EMPRESA' and agendamento.local_empresa:
                return SubSetor.objects.filter(setor__area__empresa=agendamento.local_empresa, ativo=True)
            if nivel == 'AREA' and agendamento.local_area:
                return SubSetor.objects.filter(setor__area=agendamento.local_area, ativo=True)
            if nivel == 'SETOR' and agendamento.local_setor:
                return SubSetor.objects.filter(setor=agendamento.local_setor, ativo=True)

        # Se for auditoria específica ou nível subsetor, não retorna nada
        # (pois o local já está definido)
        return SubSetor.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # Converte o queryset em dados simples (id, nome) para o Flutter
        data = list(queryset.values('id', 'nome'))
        return Response(data)


class AuditoriasConcluidasAPIView(ListAPIView):
    """
    Endpoint da API que retorna o histórico de instâncias de auditoria
    concluídas pelo usuário autenticado.
    """
    serializer_class = AuditoriaInstanciaListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filtra as instâncias para retornar apenas as que foram executadas
        pelo usuário que fez a requisição, ordenadas pela mais recente.
        """
        user = self.request.user
        return AuditoriaInstancia.objects.filter(
            executada=True,  # <-- A ÚNICA MUDANÇA É AQUI
            auditoria_agendada__responsavel=user
        ).select_related(
            'auditoria_agendada__local_empresa',
            'auditoria_agendada__local_area',
            'auditoria_agendada__local_setor',
            'auditoria_agendada__local_subsetor'
            # Ordena da mais recente para a mais antiga
        ).order_by('-data_execucao')


@login_required
def preview_audit_dates(request):
    """
    Endpoint AJAX que calcula e retorna as datas de auditoria com base
    nos parâmetros do formulário. (VERSÃO FINAL COM REPETIÇÃO AJUSTADA)
    """
    try:
        start_date_str = request.GET.get('data_inicio')
        end_date_str = request.GET.get('ate_dia')
        schedule_type = request.GET.get('schedule_type')
        frequency = request.GET.get('frequencia')
        interval_str = request.GET.get('intervalo')
        repetitions_str = request.GET.get('numero_repeticoes')
        skip_weekends = request.GET.get('pular_fins_semana') == 'true'

        if not start_date_str:
            return JsonResponse({'dates': []})

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(
            end_date_str, '%Y-%m-%d').date() if end_date_str else None

        # AQUI ESTÁ A MUDANÇA: Capturamos o número de repetições
        repetitions = int(repetitions_str) if repetitions_str and repetitions_str.isdigit(
        ) and int(repetitions_str) > 0 else 1

        dates = []
        current_date = start_date
        loop_limit = 365 * 5
        loops = 0

        if not end_date:
            if not (skip_weekends and start_date.weekday() >= 5):
                # AQUI ESTÁ A MUDANÇA: Adicionamos a data apenas UMA vez
                dates.append(start_date)
        else:
            while current_date <= end_date and loops < loop_limit:
                loops += 1

                if not (skip_weekends and current_date.weekday() >= 5):
                    # AQUI ESTÁ A MUDANÇA: Adicionamos a data apenas UMA vez
                    dates.append(current_date)

                # A lógica de cálculo da próxima data permanece a mesma
                if schedule_type == 'por_intervalo':
                    interval = int(
                        interval_str) if interval_str and interval_str.isdigit() else 0
                    current_date += timedelta(days=interval + 1)
                elif schedule_type == 'por_frequencia':
                    if frequency == 'DIARIO':
                        current_date += timedelta(days=1)
                    # ... (resto da lógica de frequência)
                    elif frequency == 'SEMANAL':
                        current_date += timedelta(weeks=1)
                    elif frequency == 'QUINZENAL':
                        current_date += timedelta(weeks=2)
                    elif frequency == 'MENSAL':
                        current_date += relativedelta(months=1)
                    elif frequency == 'ANUAL':
                        current_date += relativedelta(years=1)
                else:
                    current_date += timedelta(days=1)

        # Formatação final para a resposta JSON
        dias_semana = ["seg.", "ter.", "qua.", "qui.", "sex.", "sáb.", "dom."]
        meses = ["jan.", "fev.", "mar.", "abr.", "mai.", "jun.",
                 "jul.", "ago.", "set.", "out.", "nov.", "dez."]

        formatted_dates = [{
            'auditoria_num': i + 1,
            # <-- AQUI ESTÁ A MUDANÇA: Usamos o número de repetições para todas as linhas
            'repeticao_num': repetitions,
            'dia_semana': dias_semana[date.weekday()],
            'dia': date.strftime('%d'),
            'mes': meses[date.month - 1],
            'ano': date.year
        } for i, date in enumerate(dates)]

        return JsonResponse({'dates': formatted_dates})

    except (ValueError, TypeError) as e:
        return JsonResponse({'error': f'Parâmetros inválidos: {repr(e)}'}, status=400)


@login_required
def lista_execucoes(request):
    """Exibe o histórico de todas as instâncias de auditoria PENDENTES e ATRASADAS."""
    instancias_list = AuditoriaInstancia.objects.exclude(executada=True).select_related(
        'auditoria_agendada__responsavel',
        'auditoria_agendada__ferramenta',
        'auditoria_agendada__criado_por',
        'local_execucao',
        'responsavel'
    ).prefetch_related(
        'auditoria_agendada__modelos'
    ).order_by('data_execucao')

    search = request.GET.get('search', '')
    if search:
        instancias_list = instancias_list.filter(
            Q(auditoria_agendada__responsavel__first_name__icontains=search) |
            Q(local_execucao__nome__icontains=search) |
            Q(auditoria_agendada__modelos__descricao__icontains=search)
        ).distinct()

    paginator = Paginator(instancias_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    all_users_list = list(Usuario.objects.filter(is_active=True).annotate(
        name=Concat('first_name', Value(' '), 'last_name')
    ).values('id', 'name'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Auditorias para Execução',
        'all_users_json': json.dumps(all_users_list),
        'singular': 'Execução',
        'artigo': 'a',
        'create_url': 'auditorias:criar_auditoria',
        'button_text': 'Nova Auditoria',
        'empty_message': 'Nenhuma auditoria pendente ou atrasada encontrada.',
        'empty_subtitle': 'Todas as auditorias estão em dia!'
    }
    return render(request, 'auditorias/execucoes.html', context)


@login_required
def historico_concluidas(request):
    """Exibe o histórico de todas as instâncias de auditoria CONCLUÍDAS."""

    # A query agora filtra apenas as instâncias executadas
    instancias_list = AuditoriaInstancia.objects.filter(executada=True).select_related(
        'auditoria_agendada__responsavel',
        'auditoria_agendada__ferramenta',
    ).prefetch_related(
        'auditoria_agendada__modelos',
        'respostas'
    ).order_by('-data_execucao')

    search = request.GET.get('search', '')
    if search:
        # ... (lógica de busca pode ser adicionada aqui se necessário) ...
        pass

    paginator = Paginator(instancias_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Histórico de Auditorias Concluídas',
        'singular': 'Auditoria',
        'artigo': 'a',
        'button_text': 'Nova Auditoria',
        'create_url': 'auditorias:criar_auditoria',
        'empty_message': 'Nenhuma auditoria concluída foi encontrada.',
        'empty_subtitle': 'As auditorias finalizadas aparecerão aqui.'
    }
    return render(request, 'auditorias/historico_concluidas.html', context)


@login_required
def redirecionar_agendamento(request, pk):
    """ Redireciona o auditor de um AGENDAMENTO PAI e de todas as suas execuções filhas não concluídas. """
    if request.method == 'POST':
        novo_responsavel_id = request.POST.get('responsavel_id')
        if novo_responsavel_id:
            try:
                # Usamos .filter() para poder usar .update()
                agendamento = Auditoria.objects.filter(pk=pk)
                if not agendamento.exists():
                    messages.error(request, 'Agendamento não encontrado.')
                    return redirect(request.META.get('HTTP_REFERER', 'auditorias:lista_auditorias'))

                # 1. Atualiza o agendamento pai diretamente no banco, sem chamar o save()
                agendamento.update(responsavel_id=novo_responsavel_id)

                # 2. Atualiza todas as execuções filhas NÃO CONCLUÍDAS
                # Usamos o ID do agendamento para encontrar as instâncias corretas
                AuditoriaInstancia.objects.filter(
                    auditoria_agendada_id=pk,
                    executada=False
                ).update(responsavel_id=novo_responsavel_id)

                messages.success(
                    request, f'Agendamento #{pk} e suas execuções foram redirecionados.')
            except Exception as e:
                messages.error(request, f'Erro ao redirecionar: {e}')

    return redirect(request.META.get('HTTP_REFERER', 'auditorias:lista_auditorias'))


@login_required
def redirecionar_execucao(request, pk):
    """ Redireciona o auditor de uma ÚNICA EXECUÇÃO. """
    execucao = get_object_or_404(AuditoriaInstancia, pk=pk)
    if request.method == 'POST':
        novo_responsavel_id = request.POST.get('responsavel_id')
        if novo_responsavel_id:
            try:
                # Atualiza o responsável apenas desta execução
                execucao.responsavel_id = novo_responsavel_id
                execucao.save(update_fields=['responsavel'])
                messages.success(
                    request, f'Execução #{execucao.id} foi redirecionada com sucesso.')
            except Exception as e:
                messages.error(request, f'Erro ao redirecionar: {e}')

    return redirect(request.META.get('HTTP_REFERER', 'auditorias:lista_execucoes'))


@login_required
def deletar_execucao(request, pk):
    """ Deleta uma única instância de auditoria. """
    instancia = get_object_or_404(AuditoriaInstancia, pk=pk)
    if request.method == 'POST':
        try:
            instancia.delete()
            messages.success(
                request, f'Execução #{instancia.id} deletada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar a execução: {e}')

    # Redireciona de volta para a lista de execuções
    return redirect('auditorias:lista_execucoes')


@login_required
def detalhes_auditoria(request, pk):
    """Exibe os detalhes de uma instância de auditoria concluída."""
    try:
        # AQUI ESTÁ A CORREÇÃO: 'checklistusado' foi corrigido para 'checklist_usado'
        instancia = AuditoriaInstancia.objects.select_related(
            'auditoria_agendada__responsavel',
            'auditoria_agendada__ferramenta',
            'local_execucao__setor__area__empresa',
            'responsavel',
            'checklist_usado'  # Corrigido de 'checklistusado'
        ).prefetch_related(
            'respostas__pergunta__topico',
            'respostas__anexos'
        ).get(pk=pk)

        # Organizar as respostas por tópico para facilitar a exibição no template
        respostas_por_topico = {}
        if instancia.checklist_usado:
            for topico in instancia.checklist_usado.topicos.all().order_by('ordem'):
                respostas_por_topico[topico] = []

        for resposta in instancia.respostas.all().order_by('pergunta__ordem'):
            topico = resposta.pergunta.topico
            if topico in respostas_por_topico:
                respostas_por_topico[topico].append(resposta)

        context = {
            'instancia': instancia,
            'respostas_por_topico': respostas_por_topico,
            'title': f'Detalhes da Auditoria #{instancia.id}'
        }
        return render(request, 'auditorias/detalhes_auditoria.html', context)

    except AuditoriaInstancia.DoesNotExist:
        messages.error(
            request, 'A instância de auditoria solicitada não foi encontrada.')
        return redirect('auditorias:historico_concluidas')


@login_required
def detalhes_historico_auditoria(request, pk):
    """
    Exibe os detalhes de uma instância de auditoria concluída.
    """
    instancia = get_object_or_404(
        AuditoriaInstancia.objects.select_related(
            'checklist_usado',
            'local_execucao__setor__area__empresa',
            'auditoria_agendada__ferramenta',
            'responsavel'
        ).prefetch_related(
            'auditoria_agendada__modelos__categoria__pilar',
            'respostas__opcao_resposta',
            'respostas__anexos'
        ),
        pk=pk
    )

    respostas_map = {
        resposta.pergunta_id: resposta
        for resposta in instancia.respostas.all()
    }

    # Cálculo de Tempo
    tempo_execucao_str = "N/A"
    respostas_queryset = instancia.respostas.all()
    if respostas_queryset.count() > 1:
        datas_respostas = respostas_queryset.aggregate(
            primeira=Min('data_resposta'),
            ultima=Max('data_resposta')
        )
        if datas_respostas['primeira'] and datas_respostas['ultima']:
            delta = datas_respostas['ultima'] - datas_respostas['primeira']
            total_seconds = int(delta.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            tempo_execucao_str = f"{hours:02}:{minutes:02}:{seconds:02}"

    total_perguntas = 0
    if instancia.checklist_usado:
        total_perguntas = Pergunta.objects.filter(
            topico__checklist=instancia.checklist_usado).count()

    # --- NOVA LÓGICA DE CÁLCULO DE CONFORMIDADE ---
    # Conta quantos itens são "Não Aplicável" (NA)
    qtd_na = respostas_queryset.filter(opcao_resposta__status='NA').count()

    # Conta quantos itens são "Não Conforme" (NC)
    # Nota: Mesmo se o desvio foi solucionado, ele conta como uma Não Conformidade no histórico
    qtd_nc = respostas_queryset.filter(
        opcao_resposta__status='NAO_CONFORME').count()

    # Itens Aplicáveis = Total de perguntas respondidas - NAs
    # (Usamos o count das respostas para garantir que só conta o que foi respondido)
    total_respondido = respostas_queryset.count()
    itens_aplicaveis = total_respondido - qtd_na

    if itens_aplicaveis > 0:
        # A nota é: (Aplicáveis - Não Conformidades) / Aplicáveis
        taxa_conformidade = (
            (itens_aplicaveis - qtd_nc) / itens_aplicaveis) * 100
    else:
        taxa_conformidade = 0.0
    # -----------------------------------------------

    summary_stats = {
        'total_itens': total_perguntas,
        'nao_conformidade_maior': respostas_queryset.filter(grau_nc='NC MAIOR').count(),
        'nao_conformidade_menor': respostas_queryset.filter(grau_nc='NC MENOR').count(),
        'desvios_solucionados': respostas_queryset.filter(desvio_solucionado=True).count(),
        'oportunidades_melhoria': respostas_queryset.filter(oportunidade_melhoria=True).count(),
        'nao_aplicaveis': qtd_na,
    }

    context = {
        'title': f'Detalhes da Auditoria #{instancia.id}',
        'instancia': instancia,
        'respostas_map': respostas_map,
        'tempo_execucao': tempo_execucao_str,
        'summary_stats': summary_stats,
        # Passamos a nova variável para o template
        'taxa_conformidade': taxa_conformidade,
    }
    return render(request, 'auditorias/detalhes_historico.html', context)


@login_required
def lista_planos_de_acao(request):
    usuario = request.user

    # 1. Base da Query (Sem filtros de status ainda)
    queryset = PlanoDeAcao.objects.select_related(
        'origem_resposta__auditoria_instancia__responsavel',
        'responsavel_acao',
        'local_execucao__setor__area__empresa',
        'ferramenta',
        'categoria'
    )

    # 2. Filtro de Segurança
    if not usuario.is_superuser:
        filtro_seguranca = Q(
            responsavel_acao=usuario
        ) | Q(
            origem_resposta__auditoria_instancia__responsavel=usuario
        ) | Q(
            local_execucao__usuario_responsavel=usuario
        ) | Q(
            local_execucao__setor__usuario_responsavel=usuario
        ) | Q(
            local_execucao__setor__area__usuario_responsavel=usuario
        ) | Q(
            local_execucao__setor__area__empresa__usuario_responsavel=usuario
        )
        queryset = queryset.filter(filtro_seguranca).distinct()

    # 3. Lógica de Modos (Ativas vs Finalizadas)
    current_mode = request.GET.get('mode', 'active')  # Padrão é 'active'

    if current_mode == 'finished':
        # MODO FINALIZADAS: Mostra apenas o que acabou
        queryset = queryset.filter(
            status_plano__in=['CONCLUIDO', 'CANCELADO', 'ARQUIVADO'])

        # Contagem para os Cards de Finalizadas
        status_counts = queryset.aggregate(
            concluidas=Count('id', filter=Q(status_plano='CONCLUIDO')),
            recusadas=Count('id', filter=Q(status_plano='CANCELADO')),
            arquivadas=Count('id', filter=Q(status_plano='ARQUIVADO'))
        )

        # Mapa de filtros para Finalizadas
        status_map = {
            'concluidas': ['CONCLUIDO'],
            'recusadas': ['CANCELADO'],
            'arquivadas': ['ARQUIVADO'],
        }

    else:
        # MODO ATIVAS: Exclui o que acabou (Comportamento Padrão)
        queryset = queryset.exclude(
            status_plano__in=['CONCLUIDO', 'CANCELADO', 'ARQUIVADO'])

        # Contagem para os Cards de Ativas
        status_counts = queryset.aggregate(
            recebidas=Count('id', filter=Q(status_plano='ABERTO')),
            aguardando_validacao=Count('id', filter=Q(
                status_plano='AGUARDANDO_VALIDACAO')),
            implementacao=Count('id', filter=Q(
                status_plano='EM_IMPLEMENTACAO')),
            ag_aprovacao=Count('id', filter=Q(
                status_plano='AGUARDANDO_APROVACAO')),
            val_eficacia=Count('id', filter=Q(
                status_plano='VALIDACAO_EFICACIA'))
        )

        # Mapa de filtros para Ativas
        status_map = {
            'recebidas': ['ABERTO'],
            'validacao': ['AGUARDANDO_VALIDACAO'],
            'implementacao': ['EM_IMPLEMENTACAO'],
            'ag_aprovacao': ['AGUARDANDO_APROVACAO'],
            'val_eficacia': ['VALIDACAO_EFICACIA'],
        }

    # 4. Aplicação do Filtro de Status Específico (Clique no Card)
    status_filtro = request.GET.get('status', 'todos')
    if status_filtro != 'todos' and status_filtro in status_map:
        queryset = queryset.filter(status_plano__in=status_map[status_filtro])

    # 5. Filtros de Busca (Input de Texto)
    search_id = request.GET.get('search_id', '')
    search_auditoria_id = request.GET.get('search_auditoria_id', '')

    if search_id:
        queryset = queryset.filter(id__icontains=search_id)
    if search_auditoria_id:
        queryset = queryset.filter(
            origem_resposta__auditoria_instancia__id__icontains=search_auditoria_id)

    # 6. Paginação e Contexto
    paginator = Paginator(queryset.order_by('-data_abertura'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Lista de usuários para os modais
    usuarios_ativos = Usuario.objects.filter(is_active=True).values(
        'id', 'first_name', 'last_name', 'username')

    categorias = CategoriaAuditoria.objects.filter(ativo=True)
    subsetores = SubSetor.objects.filter(
        ativo=True).select_related('setor__area__empresa')

    context = {
        'page_obj': page_obj,
        'title': 'Histórico de Ações Finalizadas' if current_mode == 'finished' else 'Gerenciamento dos Planos de Ações',
        'status_counts': status_counts,
        'current_status': status_filtro,
        # Enviamos o modo para o template saber qual botão mostrar
        'current_mode': current_mode,
        'singular': 'Plano de Ação',
        'artigo': 'o',
        'create_url': 'auditorias:dashboard',
        'button_text': 'Novo Plano',
        'empty_message': 'Nenhum plano encontrado neste status.',
        'searches': {'id': search_id, 'auditoria_id': search_auditoria_id},
        'usuarios_ativos': usuarios_ativos,
        'categorias': categorias,
        'subsetores': subsetores,
    }
    return render(request, 'auditorias/planos_de_acao/lista.html', context)


@login_required
@require_POST
def arquivar_plano(request, pk):
    """
    Recebe uma requisição AJAX para arquivar um Plano de Ação.
    """
    plano = get_object_or_404(PlanoDeAcao, pk=pk)

    try:
        data = json.loads(request.body)
        motivo = data.get('motivo', '')

        # Atualiza o status e o motivo
        plano.status_plano = 'ARQUIVADO'
        plano.motivo_arquivamento = motivo
        plano.save()

        return JsonResponse({'status': 'success', 'message': 'Plano arquivado com sucesso!'})

    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': f'Erro ao arquivar: {str(e)}'},
            status=400
        )


@login_required
def get_detalhes_plano(request, pk):
    """Retorna dados completos do plano e da resposta de origem para o modal via AJAX"""
    plano = get_object_or_404(PlanoDeAcao, pk=pk)
    resposta = plano.origem_resposta

    lista_investimentos = []
    total_geral_investido = 0

    # =================================================================
    # 1. LÓGICA DE EVIDÊNCIAS (FOTOS)
    # =================================================================
    evidencias_origem = []
    evidencias_conclusao = []

    # Busca todas as evidências atreladas diretamente ao plano
    todas_evidencias_plano = plano.evidencias.all()

    if resposta:
        # --- CENÁRIO 1: PLANO VINDO DE AUDITORIA ---

        # A. Contexto: Pega as fotos da Resposta da Auditoria
        for anexo in resposta.anexos.all():
            evidencias_origem.append({
                'url': anexo.arquivo.url,
                'nome': anexo.arquivo.name.split('/')[-1]
            })

        # B. Conclusão: Pega as fotos anexadas no Plano (EvidenciaPlano)
        for ev in todas_evidencias_plano:
            evidencias_conclusao.append({
                'url': ev.arquivo.url,
                'nome': ev.arquivo.name.split('/')[-1]
            })

    else:
        # --- CENÁRIO 2: PLANO MANUAL (AVULSO) ---

        # A. Contexto: Como não tem auditoria, as fotos que subimos na criação (EvidenciaPlano)
        # devem aparecer aqui, como solicitado.
        for ev in todas_evidencias_plano:
            evidencias_origem.append({
                'url': ev.arquivo.url,
                'nome': ev.arquivo.name.split('/')[-1]
            })

        # B. Conclusão: Deixamos vazio por enquanto para não duplicar as imagens.
        # (Futuramente, se houver uploads na etapa de conclusão de um plano manual,
        # poderíamos diferenciar pela data de upload ou criar um campo 'tipo' no modelo)
        pass

    # =================================================================
    # 2. LÓGICA DE OBSERVAÇÃO
    # =================================================================
    texto_observacao = "Sem observações."

    if resposta:
        # Prioridade de campos da auditoria
        if resposta.descricao_desvio_nao_solucionado:
            texto_observacao = resposta.descricao_desvio_nao_solucionado
        elif resposta.descricao_oportunidade_melhoria:
            texto_observacao = resposta.descricao_oportunidade_melhoria
        elif resposta.descricao_desvio_solucionado:
            texto_observacao = resposta.descricao_desvio_solucionado
        elif resposta.resposta_livre_texto:
            texto_observacao = resposta.resposta_livre_texto
    else:
        # Plano Manual: Pega do campo de observação de origem
        if plano.observacao_origem:
            texto_observacao = plano.observacao_origem

    # =================================================================
    # 3. INVESTIMENTOS
    # =================================================================
    for inv in plano.investimentos.all().order_by('-data_registro'):
        lista_investimentos.append({
            'descricao': inv.descricao,
            'quantidade': inv.quantidade,
            'valor_unitario': float(inv.valor_unitario),
            'valor_total': float(inv.valor_total)
        })
        total_geral_investido += float(inv.valor_total)

    # =================================================================
    # 4. HISTÓRICO
    # =================================================================
    historico_data = []
    for hist in plano.historico.all():
        data_local = timezone.localtime(hist.data_registro)
        historico_data.append({
            'usuario': hist.usuario.get_full_name() if hist.usuario else "Sistema",
            'avatar': hist.usuario.first_name[0].upper() if hist.usuario and hist.usuario.first_name else "S",
            'descricao': hist.descricao,
            'data': data_local.strftime('%d/%m/%Y'),
            'hora': data_local.strftime('%H:%M'),
            'tipo': hist.tipo
        })

    forum_id = plano.forum.id if plano.forum else None

    # Monta o JSON final
    data = {
        'id': plano.id,

        # Seção de Contexto (Topo do Modal)
        'auditoria_pergunta': plano.titulo,
        'auditoria_observacao': texto_observacao,
        # <--- Agora inclui os uploads manuais aqui
        'auditoria_evidencias': evidencias_origem,

        # Seção de Tratativa
        'causa_raiz': plano.descricao_causa_raiz or '',
        'plano_acao': plano.descricao_acao or '',

        'acoes_realizadas': plano.descricao_acao_realizada or '',
        # <--- Fica vazio para manuais (evita duplicação)
        'evidencias_conclusao': evidencias_conclusao,

        'data_prevista': plano.data_finalizacao_prevista.strftime('%Y-%m-%d') if plano.data_finalizacao_prevista else '',

        'investimentos': lista_investimentos,
        'total_investido': total_geral_investido,
        'historico': historico_data,
        'forum_id': forum_id,
    }
    return JsonResponse(data)


@login_required
@require_POST
def aceitar_plano(request, pk):
    plano = get_object_or_404(PlanoDeAcao, pk=pk)
    try:
        data = json.loads(request.body)

        plano.descricao_causa_raiz = data.get('causa_raiz')
        plano.descricao_acao = data.get('acoes_propostas')

        data_fim = data.get('data_finalizacao')
        if data_fim:
            plano.data_finalizacao_prevista = data_fim

        # --- NOVA LÓGICA DE FLUXO ---
        is_simplificado = data.get('fluxo_simplificado') == True
        plano.fluxo_simplificado = is_simplificado

        if is_simplificado:
            # Pula a validação do auditor e já permite executar
            plano.status_plano = 'EM_IMPLEMENTACAO'
            msg_hist = "Aceitou o plano em Fluxo Simplificado (sem validação)."
        else:
            # Fluxo normal
            plano.status_plano = 'AGUARDANDO_VALIDACAO'
            msg_hist = "Aceitou o plano e enviou para validação."
        # ---------------------------

        plano.save()

        registrar_historico(plano, request.user, msg_hist, "STATUS")

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def aprovar_planejamento(request, pk):
    """
    O Auditor aprova o plano proposto pelo responsável.
    Status muda de AGUARDANDO_VALIDACAO -> EM_IMPLEMENTACAO
    """
    plano = get_object_or_404(PlanoDeAcao, pk=pk)

    # Opcional: Verificar permissão (se o usuário é o auditor ou superuser)
    # auditor = plano.origem_resposta.auditoria_instancia.responsavel
    # if request.user != auditor and not request.user.is_superuser:
    #    return JsonResponse({'status': 'error', 'message': 'Apenas o auditor pode aprovar.'}, status=403)

    try:
        # Atualiza o status
        plano.status_plano = 'EM_IMPLEMENTACAO'
        plano.save()

        registrar_historico(
            plano, request.user, "Aprovou o planejamento. Plano em implementação.", "STATUS")

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def adicionar_investimento(request, pk):
    plano = get_object_or_404(PlanoDeAcao, pk=pk)
    try:
        dados = json.loads(request.body)

        # Verifica se recebeu uma lista (novo padrão) ou objeto único (legado/segurança)
        items = dados if isinstance(dados, list) else [dados]

        objs = []
        for item in items:
            descricao = item.get('descricao')
            if not descricao:
                continue  # Pula itens vazios se houver

            objs.append(Investimento(
                plano=plano,
                descricao=descricao,
                quantidade=int(item.get('quantidade', 1)),
                valor_unitario=float(
                    str(item.get('preco', 0)).replace(',', '.'))
            ))

        # Salva tudo de uma vez
        if objs:
            Investimento.objects.bulk_create(objs)

        return JsonResponse({'status': 'success', 'message': f'{len(objs)} investimentos registrados!'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def concluir_planejamento(request, pk):
    plano = get_object_or_404(PlanoDeAcao, pk=pk)

    try:
        acoes_realizadas = request.POST.get('acoes_realizadas')
        if acoes_realizadas:
            plano.descricao_acao_realizada = acoes_realizadas

        arquivos = request.FILES.getlist('evidencias')
        if arquivos:
            for f in arquivos:
                EvidenciaPlano.objects.create(plano=plano, arquivo=f)

        # --- NOVA LÓGICA DE FLUXO ---
        if plano.fluxo_simplificado:
            # Finaliza direto
            plano.status_plano = 'CONCLUIDO'
            plano.data_conclusao = timezone.now()
            msg_hist = "Concluiu a implementação. Plano finalizado automaticamente (Fluxo Simplificado)."
        else:
            # Vai para aprovação do auditor
            plano.status_plano = 'AGUARDANDO_APROVACAO'
            # (Data conclusão real só é setada quando o auditor aprovar de fato, ou aqui como provisória)
            plano.data_conclusao = timezone.now()
            msg_hist = "Concluiu a implementação e enviou para aprovação."
        # ---------------------------

        plano.save()

        registrar_historico(plano, request.user, msg_hist, "ANEXO")

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def avaliar_conclusao(request, pk):
    """
    O Auditor decide se finaliza o plano ou envia para validação de eficácia.
    """
    plano = get_object_or_404(PlanoDeAcao, pk=pk)

    try:
        data = json.loads(request.body)
        decisao = data.get('decisao')  # 'finalizar' ou 'eficacia'

        if decisao == 'finalizar':
            plano.status_plano = 'CONCLUIDO'
            # Garante que a data de conclusão final é hoje
            plano.data_conclusao = timezone.now()

            registrar_historico(plano, request.user,
                                "Finalizou o plano de ação.", "STATUS")

        elif decisao == 'eficacia':
            plano.status_plano = 'VALIDACAO_EFICACIA'
            # Opcional: Limpar data de conclusão pois o processo continuará
            # plano.data_conclusao = None

            registrar_historico(plano, request.user,
                                "Enviou para validação de eficácia.", "STATUS")

        else:
            return JsonResponse({'status': 'error', 'message': 'Decisão inválida'}, status=400)

        plano.save()
        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def validar_eficacia(request, pk):
    """
    Etapa Final: Validação da Eficácia.
    Status muda de VALIDACAO_EFICACIA -> CONCLUIDO
    """
    plano = get_object_or_404(PlanoDeAcao, pk=pk)

    try:
        # 1. Salva a observação
        obs = request.POST.get('observacao_eficacia')
        if obs:
            plano.observacao_eficacia = obs

        # 2. Salva as evidências de eficácia (adiciona à lista existente)
        arquivos = request.FILES.getlist('evidencias')
        if arquivos:
            for f in arquivos:
                EvidenciaPlano.objects.create(plano=plano, arquivo=f)

        # 3. Finaliza o Plano
        plano.status_plano = 'CONCLUIDO'
        plano.data_conclusao = timezone.now()  # Data real do fim do ciclo
        plano.save()

        registrar_historico(plano, request.user,
                            "Validou a eficácia e concluiu o plano.", "STATUS")

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def recusar_plano(request, pk):
    """
    Recusa a etapa atual e retorna ao status anterior.
    Se estiver em ABERTO, vai para CANCELADO (some da lista).
    """
    plano = get_object_or_404(PlanoDeAcao, pk=pk)

    try:
        data = json.loads(request.body)
        motivo = data.get('motivo')

        if motivo:
            # Salva o motivo (pode-se concatenar com histórico se desejar)
            plano.motivo_recusa = motivo

        # --- LÓGICA DE RETORNO ---
        status_atual = plano.status_plano

        if status_atual == 'ABERTO':
            # Responsável rejeitou o plano logo de cara
            plano.status_plano = 'CANCELADO'

        elif status_atual == 'AGUARDANDO_VALIDACAO':
            # Auditor rejeitou o planejamento -> Volta para o Responsável planejar
            plano.status_plano = 'ABERTO'

        elif status_atual == 'AGUARDANDO_APROVACAO':
            # Auditor rejeitou a execução -> Volta para Implementação (fazer de novo/melhorar)
            plano.status_plano = 'EM_IMPLEMENTACAO'

        elif status_atual == 'VALIDACAO_EFICACIA':
            # Se rejeitar a eficácia, volta para aprovação (ou implementação, depende da regra)
            # Geralmente volta para o Auditor decidir o que fazer, ou para implementação
            plano.status_plano = 'AGUARDANDO_APROVACAO'

        plano.save()

        registrar_historico(
            plano, request.user, f"Recusou/Devolveu a etapa. Motivo: {motivo}", "STATUS")

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def clonar_plano(request, pk):
    """
    Duplica um plano de ação existente, resetando o status para ABERTO
    e atribuindo um novo responsável.
    """
    plano_original = get_object_or_404(PlanoDeAcao, pk=pk)

    try:
        data = json.loads(request.body)
        novo_responsavel_id = data.get('novo_responsavel')
        orientacoes = data.get('orientacoes')

        if not novo_responsavel_id or not orientacoes:
            return JsonResponse({'status': 'error', 'message': 'Dados incompletos'}, status=400)

        # --- LÓGICA DE CLONAGEM ---
        # 1. Copia o objeto (colocando pk=None, o Django cria um novo ao salvar)
        novo_plano = plano_original
        novo_plano.pk = None
        novo_plano.id = None

        # 2. Define os novos dados
        novo_plano.responsavel_acao_id = novo_responsavel_id
        novo_plano.orientacoes_extra = orientacoes

        novo_plano.origem_orientacao = 'CLONAGEM'

        # 3. Reseta para o estado inicial (Como se fosse novo)
        novo_plano.status_plano = 'ABERTO'
        novo_plano.data_abertura = timezone.now()

        # 4. Limpa dados de execução/histórico do antigo
        novo_plano.prazo_conclusao = None  # Ou mantém o prazo original, você decide
        novo_plano.data_conclusao = None
        novo_plano.descricao_causa_raiz = None
        novo_plano.descricao_acao = None
        novo_plano.descricao_acao_realizada = None
        novo_plano.observacao_eficacia = None
        novo_plano.motivo_recusa = None
        novo_plano.motivo_arquivamento = None
        novo_plano.data_finalizacao_prevista = None

        # 5. Cria um NOVO Fórum (Importante! Não podem compartilhar o chat)
        novo_forum = Forum.objects.create(
            nome=f"Discussão Plano Clonado - {novo_plano.titulo[:30]}..."
        )
        novo_plano.forum = novo_forum

        novo_plano.save()

        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def alterar_prazo(request, pk):
    """
    Altera a data de finalização prevista do plano de ação.
    """
    plano = get_object_or_404(PlanoDeAcao, pk=pk)

    try:
        data = json.loads(request.body)
        nova_data = data.get('nova_data')

        if nova_data:
            plano.data_finalizacao_prevista = nova_data
            # Se quiser atualizar também o prazo oficial (prazo_conclusao), descomente abaixo:
            # plano.prazo_conclusao = nova_data
            plano.save()
            data_fmt = datetime.strptime(
                nova_data, '%Y-%m-%d').strftime('%d/%m/%Y')
            registrar_historico(
                plano, request.user, f"Alterou a data prevista para {data_fmt}.", "PRAZO")
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Data inválida'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def redirecionar_plano(request, pk):
    """
    Transfere a responsabilidade do plano para outro usuário.
    MANTÉM o status atual do plano.
    """
    plano = get_object_or_404(PlanoDeAcao, pk=pk)

    try:
        data = json.loads(request.body)
        novo_responsavel_id = data.get('novo_responsavel')
        acoes_sugeridas = data.get('acoes_sugeridas')

        if not novo_responsavel_id:
            return JsonResponse({'status': 'error', 'message': 'Novo responsável é obrigatório'}, status=400)

        # 1. Atualiza o responsável
        plano.responsavel_acao_id = novo_responsavel_id

        # 2. Salva as ações sugeridas
        if acoes_sugeridas:
            plano.orientacoes_extra = acoes_sugeridas

            plano.origem_orientacao = 'REDIRECIONAMENTO'

        # 3. STATUS: Mantemos o que já estava.
        # A linha abaixo foi removida para atender sua solicitação:
        # plano.status_plano = 'ABERTO'

        plano.save()

        novo_nome = plano.responsavel_acao.get_full_name()
        registrar_historico(
            plano, request.user, f"Redirecionou a ação para {novo_nome}.", "REDISTRIBUICAO")

        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# 1. API para LISTAR mensagens (Retorna JSON)
@login_required
def api_listar_mensagens(request, forum_id):
    try:
        forum = Forum.objects.get(id=forum_id)
        # Verifica permissão se necessário

        mensagens = []
        for msg in forum.mensagens.all().order_by('data_envio'):
            mensagens.append({
                'id': msg.id,
                'autor': msg.autor.get_full_name() or msg.autor.username,
                'conteudo': msg.conteudo,
                'data_envio': msg.data_envio.strftime('%d/%m/%Y às %H:%M'),
                'is_me': msg.autor == request.user  # Para pintar de cor diferente
            })

        return JsonResponse({'mensagens': mensagens})
    except Forum.DoesNotExist:
        return JsonResponse({'error': 'Fórum não encontrado'}, status=404)

# 2. API para ENVIAR mensagem (Recebe JSON)


@login_required
@require_POST
def api_enviar_mensagem(request, forum_id):
    try:
        forum = get_object_or_404(Forum, id=forum_id)
        data = json.loads(request.body)
        conteudo = data.get('conteudo')

        if conteudo:
            MensagemForum.objects.create(
                forum=forum,
                autor=request.user,
                conteudo=conteudo
            )
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Conteúdo vazio'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def criar_plano_manual(request):
    try:
        titulo = request.POST.get('titulo')
        categoria_id = request.POST.get('categoria')
        responsavel_id = request.POST.get('responsavel')
        local_id = request.POST.get('local')
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')  # Data do modal (Previsão)
        observacao = request.POST.get('observacao')

        if not titulo or not responsavel_id or not data_fim or not categoria_id:
            return JsonResponse({'status': 'error', 'message': 'Preencha os campos obrigatórios.'}, status=400)

        # Busca a ferramenta fixa
        ferramenta_obj, created = FerramentaDigital.objects.get_or_create(
            nome="Plano de Ação")

        novo_plano = PlanoDeAcao(
            titulo=titulo,
            responsavel_acao_id=responsavel_id,
            categoria_id=categoria_id,
            local_execucao_id=local_id,
            ferramenta=ferramenta_obj,

            # REGRAS DE AUDITOR E OBSERVAÇÃO
            criado_por=request.user,          # O usuário logado é o Auditor
            observacao_origem=observacao,     # Vai para observação, não para planejamento

            data_abertura=data_inicio or timezone.now(),

            # REGRAS DE DATA
            prazo_conclusao=None,             # Data Final permanece em branco
            data_finalizacao_prevista=data_fim,  # Preenche apenas a previsão

            descricao_acao=None,              # Planejamento começa vazio
            status_plano='ABERTO',
            tipo='NAO_CONFORMIDADE'
        )

        # Cria Fórum
        novo_forum = Forum.objects.create(
            nome=f"Discussão Plano Manual - {titulo[:30]}...")
        novo_plano.forum = novo_forum

        novo_plano.save()

        # Uploads
        arquivos = request.FILES.getlist('arquivos')
        for f in arquivos:
            EvidenciaPlano.objects.create(plano=novo_plano, arquivo=f)

        registrar_historico(novo_plano, request.user,
                            "Plano de ação criado manualmente.", "CRIACAO")

        return JsonResponse({'status': 'success', 'message': 'Plano criado com sucesso!'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def dashboard_planos_de_acao(request):
    # 1. QuerySets Base
    # Filtra apenas o que o usuário pode ver (reaproveitando lógica de segurança se necessário)
    qs_total = PlanoDeAcao.objects.all()

    # Pendentes: Tudo que não está finalizado
    status_pendentes = ['ABERTO', 'AGUARDANDO_VALIDACAO',
                        'EM_IMPLEMENTACAO', 'AGUARDANDO_APROVACAO', 'VALIDACAO_EFICACIA']
    qs_pendentes = qs_total.filter(status_plano__in=status_pendentes)

    # 2. KPIs (Cards da Esquerda)
    total_pendentes = qs_pendentes.count()

    # Colaboradores distintos com ações pendentes
    colaboradores_pendentes = qs_pendentes.values(
        'responsavel_acao').distinct().count()

    total_geral = qs_total.count()
    porcentagem_pendentes = (
        total_pendentes / total_geral * 100) if total_geral > 0 else 0

    # 3. Gráfico: Ações Pendentes por Status (Pizza)
    status_data = qs_pendentes.values('status_plano').annotate(qtd=Count('id'))
    # Você pode mapear para nomes amigáveis depois
    status_labels = [s['status_plano'] for s in status_data]
    status_series = [s['qtd'] for s in status_data]

    # 4. Gráfico: Total de Ações Geradas por Mês (Barras)
    # Pega os últimos 12 meses
    historico_mes = qs_total.annotate(
        mes=TruncMonth('data_abertura')
    ).values('mes').annotate(qtd=Count('id')).order_by('mes')

    meses_labels = [h['mes'].strftime('%b/%Y') for h in historico_mes]
    meses_series = [h['qtd'] for h in historico_mes]

    # 5. Gráfico: Ações por Ferramenta (Barras Horizontais)
    ferramentas_data = qs_total.values('ferramenta__nome').annotate(
        qtd=Count('id')).order_by('-qtd')[:10]
    ferramenta_labels = [f['ferramenta__nome'] for f in ferramentas_data]
    ferramenta_series = [f['qtd'] for f in ferramentas_data]

    # 6. Gráfico: Ações por Local (Pareto/Barras) - Usando Subsetor
    locais_data = qs_total.values('local_execucao__nome').annotate(
        qtd=Count('id')).order_by('-qtd')[:10]
    local_labels = [l['local_execucao__nome'] for l in locais_data]
    local_series = [l['qtd'] for l in locais_data]

    # 7. Ranking de Usuários (Top 5 Pendentes)
    ranking_data = qs_pendentes.values(
        'responsavel_acao__first_name', 'responsavel_acao__last_name', 'responsavel_acao__username'
    ).annotate(qtd=Count('id')).order_by('-qtd')[:5]

    ranking_list = []
    for r in ranking_data:
        nome = f"{r['responsavel_acao__first_name']} {r['responsavel_acao__last_name']}".strip()
        if not nome:
            nome = r['responsavel_acao__username']
        ranking_list.append({'nome': nome, 'qtd': r['qtd']})

    context = {
        'title': 'Dashboard de Planos de Ação',
        'kpi_total_pendentes': total_pendentes,
        'kpi_colaboradores': colaboradores_pendentes,
        'kpi_porcentagem': f"{porcentagem_pendentes:.1f}%",

        # Dados para JS (converteremos no template com json_script ou direto)
        'chart_status_labels': json.dumps(status_labels),
        'chart_status_series': json.dumps(status_series),

        'chart_mes_labels': json.dumps(meses_labels),
        'chart_mes_series': json.dumps(meses_series),

        'chart_ferramenta_labels': json.dumps(ferramenta_labels),
        'chart_ferramenta_series': json.dumps(ferramenta_series),

        'chart_local_labels': json.dumps(local_labels),
        'chart_local_series': json.dumps(local_series),

        'ranking_list': ranking_list,
    }

    return render(request, 'auditorias/planos_de_acao/dashboard.html', context)


@login_required
def get_dados_calendario(request):
    """Retorna dados para o calendário de auditorias via AJAX - Com Status de Atraso"""
    try:
        ano = int(request.GET.get('year', timezone.now().year))
        mes = int(request.GET.get('month', timezone.now().month))

        instancias = AuditoriaInstancia.objects.filter(
            data_execucao__year=ano,
            data_execucao__month=mes
        )

        dados_dias = {}

        for inst in instancias:
            dia = inst.data_execucao.day
            status_real = inst.status_execucao

            # --- LÓGICA ATUALIZADA (4 STATUS) ---
            if status_real == 'Concluída':
                label = 'Concluído'
                cor = 'success'   # Verde
            elif status_real == 'Atraso':
                label = 'Não realizado'
                cor = 'danger'    # Vermelho
            elif status_real == 'Pendente':
                label = 'Pendente'
                cor = 'warning'   # Laranja
            else:
                # Agendada, Em andamento, etc. viram Planejado
                label = 'Planejado'
                cor = 'secondary'  # Cinza

            if dia not in dados_dias:
                dados_dias[dia] = {}

            chave_status = f"{label}|{cor}"
            dados_dias[dia][chave_status] = dados_dias[dia].get(
                chave_status, 0) + 1

        return JsonResponse({
            'dados': dados_dias,
            'sucesso': True
        })
    except Exception as e:
        return JsonResponse({'sucesso': False, 'erro': str(e)})
