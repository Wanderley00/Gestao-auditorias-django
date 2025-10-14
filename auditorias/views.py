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

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .serializers import RespostaSerializer

# Altere ListAPIView para incluir RetrieveAPIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
# Altere a importação dos serializers
from .serializers import AuditoriaInstanciaListSerializer, AuditoriaInstanciaDetailSerializer

from .models import (
    Pilar, CategoriaAuditoria, Norma, RequisitoNorma, FerramentaDigital,
    Checklist, Topico, Pergunta, OpcaoResposta, OpcaoPorcentagem,
    FerramentaCausaRaiz, ModeloAuditoria, Auditoria, AuditoriaInstancia, Resposta,
    CATEGORIAS_AUDITORIA
)
from organizacao.models import Empresa, Area, Setor, SubSetor
from ativos.models import Ativo
from cadastros_base.models import Turno
from usuarios.models import Usuario

import json

from django.db.models import Q, F, Value
from django.db.models.functions import Concat

from django.utils import timezone

from django.db import transaction

# ============================================================================
# VIEWS PRINCIPAIS - DASHBOARD E LISTAGENS
# ============================================================================


@login_required
def dashboard_auditorias(request):
    """Dashboard principal do módulo de auditorias"""
    context = {
        'total_auditorias': Auditoria.objects.count(),
        'total_modelos': ModeloAuditoria.objects.count(),
        'total_checklists': Checklist.objects.count(),
        'total_pilares': Pilar.objects.count(),
        'auditorias_recentes': Auditoria.objects.order_by('-data_criacao')[:5],
        'instancias_pendentes': AuditoriaInstancia.objects.filter(executada=False).count(),
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
    Cria uma nova versão de um checklist populando-a diretamente
    com os dados do request.POST, evitando conflitos de ID.
    """
    # 1. Cria o novo objeto Checklist (a nova versão)
    nova_versao = Checklist.objects.create(
        nome=request.POST.get('nome'),
        ativo=request.POST.get('ativo') == 'on',
        ferramenta_id=request.POST.get('ferramenta') or None,
        version=checklist_original.version + 1,
        is_latest=True,
        original_checklist=checklist_original.original_checklist or checklist_original
    )

    # 2. Re-processa a estrutura do formulário, mas criando tudo para a nova versão
    topicos_data = {}
    for key in request.POST:
        if key.startswith('topico-descricao['):
            # ID do formulário (pode ser '123' ou 'new-1')
            topico_id_form = key.split('[')[1].split(']')[0]
            topicos_data[topico_id_form] = {
                'descricao': request.POST.get(key),
                'ordem': request.POST.get(f'topico-ordem[{topico_id_form}]', 0)
            }

    for topico_id_form, topico_info in topicos_data.items():
        # Cria um novo tópico para a nova versão
        novo_topico = Topico.objects.create(
            checklist=nova_versao,
            descricao=topico_info['descricao'],
            ordem=int(topico_info['ordem']) if topico_info['ordem'] else 0
        )

        # Processa as perguntas associadas a este tópico no formulário
        for key in request.POST:
            if key.startswith(f'pergunta-descricao[{topico_id_form}-'):
                pergunta_id_full = key.split('[')[1].split(']')[0]

                # Cria uma nova pergunta para o novo tópico
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

                # Processa as opções de resposta para esta pergunta
                for opt_key in request.POST:
                    if opt_key.startswith(f'opcao-resposta-descricao[{pergunta_id_full}-'):
                        opt_id_full = opt_key.split('[')[1].split(']')[0]
                        OpcaoResposta.objects.create(
                            pergunta=nova_pergunta,
                            descricao=request.POST.get(opt_key),
                            status=request.POST.get(
                                f'opcao-resposta-status[{opt_id_full}]', 'CONFORME')
                        )

                # Processa as opções de porcentagem para esta pergunta
                for opt_key in request.POST:
                    if opt_key.startswith(f'opcao-porcentagem-descricao[{pergunta_id_full}-'):
                        opt_id_full = opt_key.split('[')[1].split(']')[0]
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
    e atualiza as auditorias futuras.
    """
    checklist_antigo = get_object_or_404(Checklist, pk=pk)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Cria a nova versão diretamente a partir dos dados do formulário
                novo_checklist = _create_new_version_from_request(
                    request, checklist_antigo)

                # 2. Desativa a versão antiga, marcando-a como não sendo a mais recente
                checklist_antigo.is_latest = False
                checklist_antigo.save()

                # 3. Encontra todos os Modelos de Auditoria que usavam a versão antiga
                modelos_afetados_ids = list(ModeloAuditoria.objects.filter(
                    checklist=checklist_antigo
                ).values_list('id', flat=True))

                if modelos_afetados_ids:
                    # 5. Atualiza esses modelos para apontarem para o NOVO checklist
                    ModeloAuditoria.objects.filter(
                        id__in=modelos_afetados_ids).update(checklist=novo_checklist)

                    # 6. Atualiza APENAS as instâncias de auditoria com status "Agendada"
                    #    (ou seja, com data estritamente maior que hoje)
                    AuditoriaInstancia.objects.filter(
                        auditoria_agendada__modelos__id__in=modelos_afetados_ids,
                        executada=False,
                        # --- ESTA É A LINHA QUE VAMOS ALTERAR ---
                        data_execucao__gt=timezone.now().date()  # Alterado de __gte para __gt
                    ).update(checklist_usado=novo_checklist)

                messages.success(
                    request, f'Checklist "{novo_checklist.nome}" atualizado para a versão {novo_checklist.version} com sucesso!')
                return redirect('auditorias:lista_checklists')

        except Exception as e:
            messages.error(request, f'Erro ao atualizar checklist: {repr(e)}')
            import traceback
            print(traceback.format_exc())

    # O contexto para o método GET continua o mesmo
    context = {
        'checklist': checklist_antigo,
        'object': checklist_antigo,
        'ferramentas': FerramentaDigital.objects.all(),
        'status_opcoes': OpcaoResposta._meta.get_field('status').choices,
        'title': f'Editar Checklist: {checklist_antigo.nome} (V{checklist_antigo.version})',
        'back_url': 'auditorias:lista_checklists'
    }
    return render(request, 'auditorias/checklists/form.html', context)


# Supondo que seus models (AuditoriaInstancia, Checklist, SubSetor, Topico, etc.)
# estejam importados corretamente.
# from .models import AuditoriaInstancia, Checklist, SubSetor, Topico, Pergunta, OpcaoResposta, OpcaoPorcentagem


def _gerar_instancias_para_auditoria(auditoria):
    """
    Função responsável por apagar instâncias futuras e gerar as novas
    com base nos parâmetros do agendamento de uma auditoria.
    Esta função deve ser chamada DEPOIS que a auditoria e seus M2M estiverem salvos.
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
            loop_limit = 365 * 5  # Limite de 5 anos para evitar loops infinitos
            loops = 0
            while current_date <= end_date and loops < loop_limit:
                loops += 1
                if not (auditoria.pular_finais_semana and current_date.weekday() >= 5):
                    dates_to_create.append(current_date)

                if auditoria.por_intervalo and auditoria.intervalo:
                    current_date += timedelta(days=auditoria.intervalo + 1)
                elif auditoria.por_frequencia and auditoria.frequencia:
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
    if auditoria.nivel_organizacional == 'SUBSETOR' and auditoria.local_subsetor:
        target_locations.append(auditoria.local_subsetor)
    elif auditoria.nivel_organizacional == 'SETOR' and auditoria.local_setor:
        target_locations = list(
            auditoria.local_setor.subsetor_set.filter(ativo=True))
    elif auditoria.nivel_organizacional == 'AREA' and auditoria.local_area:
        target_locations = list(SubSetor.objects.filter(
            setor__area=auditoria.local_area, ativo=True))
    elif auditoria.nivel_organizacional == 'EMPRESA' and auditoria.local_empresa:
        target_locations = list(SubSetor.objects.filter(
            setor__area__empresa=auditoria.local_empresa, ativo=True))

    if not target_locations:
        target_locations.append(None)

    target_turnos = list(auditoria.turnos.all())
    if not target_turnos:
        target_turnos.append(None)

    repetitions = auditoria.numero_repeticoes if auditoria.numero_repeticoes and auditoria.numero_repeticoes > 0 else 1

    # 5. Cria as novas instâncias
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
    """Lista todas as versões de um checklist específico."""
    checklist_atual = get_object_or_404(Checklist, pk=pk)

    # Encontra o checklist original (V1) para buscar todas as suas versões
    original = checklist_atual.original_checklist or checklist_atual

    # Busca todas as versões relacionadas, incluindo o original, ordenando da mais nova para a mais antiga
    versoes = original.versions.all() | Checklist.objects.filter(pk=original.pk)
    versoes = versoes.order_by('-version')

    context = {
        'page_obj': versoes,  # Usando page_obj para reutilizar o template
        'original': original,
        'title': f'Histórico de Versões: {original.nome}',
        # Apenas para o template não quebrar
        'create_url': 'auditorias:criar_checklist',
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
    Retorna um dicionário com as diferenças detectadas.
    """
    comparacao = {
        'versoes_info': [],
        'topicos_diff': [],
        'alteracoes_resumo': {
            'topicos_adicionados': 0,
            'topicos_removidos': 0,
            'perguntas_adicionadas': 0,
            'perguntas_removidas': 0,
            'perguntas_modificadas': 0,
        }
    }

    # Informações básicas de cada versão
    for v in versoes:
        comparacao['versoes_info'].append({
            'id': v.pk,
            'version': v.version,
            'nome': v.nome,
            'data': v.data_cadastro,
            'total_topicos': v.topicos.count(),
            'total_perguntas': sum(t.perguntas.count() for t in v.topicos.all()),
        })

    # Análise detalhada das diferenças
    if len(versoes) >= 2:
        # Compara tópicos
        todas_versoes_topicos = {}
        for v in versoes:
            todas_versoes_topicos[v.version] = {
                t.descricao: {
                    'ordem': t.ordem,
                    'perguntas': {
                        p.descricao: {
                            'ordem': p.ordem,
                            'obrigatoria': p.obrigatoria,
                            'resposta_livre': p.resposta_livre,
                            'foto': p.foto,
                            'criar_opcao': p.criar_opcao,
                            'porcentagem': p.porcentagem,
                            'opcoes_resposta': [{'descricao': o.descricao, 'status': o.status}
                                                for o in p.opcoes_resposta.all()],
                            'opcoes_porcentagem': [{'descricao': o.descricao, 'peso': o.peso}
                                                   for o in p.opcoes_porcentagem.all()],
                        } for p in t.perguntas.all()
                    }
                } for t in v.topicos.all()
            }

        # Detecta tópicos adicionados/removidos
        versao_base = list(versoes)[0]
        versao_comparada = list(versoes)[-1]

        topicos_base = set(todas_versoes_topicos[versao_base.version].keys())
        topicos_comparada = set(
            todas_versoes_topicos[versao_comparada.version].keys())

        topicos_adicionados = topicos_comparada - topicos_base
        topicos_removidos = topicos_base - topicos_comparada
        topicos_comuns = topicos_base & topicos_comparada

        comparacao['alteracoes_resumo']['topicos_adicionados'] = len(
            topicos_adicionados)
        comparacao['alteracoes_resumo']['topicos_removidos'] = len(
            topicos_removidos)

        # Analisa perguntas em tópicos comuns
        for topico_desc in topicos_comuns:
            perguntas_base = set(
                todas_versoes_topicos[versao_base.version][topico_desc]['perguntas'].keys())
            perguntas_comparada = set(
                todas_versoes_topicos[versao_comparada.version][topico_desc]['perguntas'].keys())

            perguntas_adicionadas = perguntas_comparada - perguntas_base
            perguntas_removidas = perguntas_base - perguntas_comparada
            perguntas_comuns = perguntas_base & perguntas_comparada

            comparacao['alteracoes_resumo']['perguntas_adicionadas'] += len(
                perguntas_adicionadas)
            comparacao['alteracoes_resumo']['perguntas_removidas'] += len(
                perguntas_removidas)

            # Detecta perguntas modificadas
            for pergunta_desc in perguntas_comuns:
                perg_base = todas_versoes_topicos[versao_base.version][topico_desc]['perguntas'][pergunta_desc]
                perg_comp = todas_versoes_topicos[versao_comparada.version][topico_desc]['perguntas'][pergunta_desc]

                if perg_base != perg_comp:
                    comparacao['alteracoes_resumo']['perguntas_modificadas'] += 1

        # Estrutura detalhada para exibição
        comparacao['topicos_diff'] = todas_versoes_topicos

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
    """Cria uma nova auditoria agendada"""
    if request.method == 'POST':
        # --- Captura todos os dados do formulário primeiro ---
        ferramenta_id = request.POST.get('ferramenta')
        responsavel_id = request.POST.get('responsavel')
        nivel_organizacional = request.POST.get('nivel_organizacional')
        data_inicio_str = request.POST.get('data_inicio')
        data_fim_str = request.POST.get('data_fim')

        local_empresa_id = request.POST.get('local_empresa') or None
        local_area_id = request.POST.get('local_area') or None
        local_setor_id = request.POST.get('local_setor') or None
        local_subsetor_id = request.POST.get('local_subsetor') or None

        modelos_ids = request.POST.getlist('modelos')
        ativos_ids = request.POST.getlist('ativos_auditados')
        turnos_ids = request.POST.getlist('turnos')

        if ferramenta_id and responsavel_id and nivel_organizacional and data_inicio_str:
            try:
                data_inicio = datetime.strptime(
                    data_inicio_str, '%Y-%m-%d').date()
                data_fim = datetime.strptime(
                    data_fim_str, '%Y-%m-%d').date() if data_fim_str else None

                schedule_type = request.POST.get('schedule_type')

                with transaction.atomic():

                    # --- Monta o objeto com TODOS os dados ANTES de salvar ---
                    auditoria = Auditoria(
                        criado_por=request.user,
                        ferramenta_id=ferramenta_id,
                        responsavel_id=responsavel_id,
                        nivel_organizacional=nivel_organizacional,
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                        # Atribui todos os locais aqui
                        local_empresa_id=local_empresa_id,
                        local_area_id=local_area_id,
                        local_setor_id=local_setor_id,
                        local_subsetor_id=local_subsetor_id,
                        # Outros campos...
                        categoria_auditoria=request.POST.get(
                            'categoria_auditoria'),
                        por_frequencia=schedule_type == 'por_frequencia',
                        por_intervalo=schedule_type == 'por_intervalo',
                        frequencia=request.POST.get('frequencia') or None,
                        intervalo=int(request.POST.get('intervalo')
                                      ) if request.POST.get('intervalo') else None,
                        numero_repeticoes=int(request.POST.get('numero_repeticoes')) if request.POST.get(
                            'numero_repeticoes') else None,
                        pular_finais_semana=request.POST.get(
                            'pular_finais_semana') == 'on',
                        contem_turnos=request.POST.get('contem_turnos') == 'on'
                    )

                    # --- Salva TUDO de uma vez (isso também dispara a criação das instâncias) ---
                    auditoria.save()

                    # Define as relações ManyToMany DEPOIS do primeiro save
                    if modelos_ids:
                        auditoria.modelos.set(modelos_ids)
                    if ativos_ids:
                        auditoria.ativos_auditados.set(ativos_ids)
                    if turnos_ids:
                        auditoria.turnos.set(turnos_ids)

                    # --- CHAMA A NOVA FUNÇÃO AQUI ---
                    _gerar_instancias_para_auditoria(auditoria)

                messages.success(request, 'Auditoria criada com sucesso!')
                return redirect('auditorias:lista_auditorias')

            except Exception as e:
                messages.error(request, f'Erro ao criar auditoria: {repr(e)}')
        else:
            messages.error(request, 'Campos obrigatórios não preenchidos!')

    # O contexto para o método GET continua o mesmo
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
    """Edita uma auditoria existente"""
    auditoria = get_object_or_404(Auditoria, pk=pk)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # --- Captura todos os dados do formulário primeiro ---
                data_inicio_str = request.POST.get('data_inicio')
                data_fim_str = request.POST.get('data_fim')

                # --- Atualiza todos os campos do objeto ANTES de salvar ---
                auditoria.ferramenta_id = request.POST.get('ferramenta')
                auditoria.responsavel_id = request.POST.get('responsavel')
                auditoria.nivel_organizacional = request.POST.get(
                    'nivel_organizacional')
                auditoria.categoria_auditoria = request.POST.get(
                    'categoria_auditoria')

                # Converte as datas de string para objeto de data
                auditoria.data_inicio = datetime.strptime(
                    data_inicio_str, '%Y-%m-%d').date()
                auditoria.data_fim = datetime.strptime(
                    data_fim_str, '%Y-%m-%d').date() if data_fim_str else None

                # Atualiza todos os locais
                auditoria.local_empresa_id = request.POST.get(
                    'local_empresa') or None
                auditoria.local_area_id = request.POST.get(
                    'local_area') or None
                auditoria.local_setor_id = request.POST.get(
                    'local_setor') or None
                auditoria.local_subsetor_id = request.POST.get(
                    'local_subsetor') or None

                schedule_type = request.POST.get('schedule_type')

                # Atualiza os dados de programação
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

                # --- Salva TUDO de uma vez (isso também vai recriar as instâncias futuras) ---
                auditoria.save()

                # Atualiza as relações ManyToMany
                auditoria.modelos.set(request.POST.getlist('modelos'))
                auditoria.ativos_auditados.set(
                    request.POST.getlist('ativos_auditados'))
                auditoria.turnos.set(request.POST.getlist('turnos'))

                # --- CHAMA A NOVA FUNÇÃO AQUI ---
                # Ela internamente já apaga as futuras e recria as novas
                _gerar_instancias_para_auditoria(auditoria)

            messages.success(request, 'Auditoria atualizada com sucesso!')
            return redirect('auditorias:lista_auditorias')

        except Exception as e:
            messages.error(request, f'Erro ao atualizar auditoria: {repr(e)}')

    # O contexto para o método GET (para exibir o formulário preenchido)
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
    """
    Endpoint para submeter as respostas de uma instância de auditoria.
    """
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

        respostas_data = request.data.get('respostas', [])

        # Passamos a instância para o serializer através do "contexto"
        contexto = {'auditoria_instancia': instancia}

        respostas_serializer = RespostaSerializer(
            data=respostas_data, many=True, context=contexto)

        if respostas_serializer.is_valid():
            # O método .save() agora vai chamar o método .create() que escrevemos no serializer
            respostas_serializer.save()

            # Marcamos a auditoria como executada
            instancia.executada = True
            instancia.save()

            return Response(
                {"detail": "Auditoria submetida com sucesso!"},
                status=status.HTTP_200_OK
            )

        return Response(respostas_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
