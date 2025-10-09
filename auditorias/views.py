# auditorias/views.py

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
    FerramentaCausaRaiz, ModeloAuditoria, Auditoria, AuditoriaInstancia, Resposta
)
from organizacao.models import Empresa, Area, Setor, SubSetor
from ativos.models import Ativo
from cadastros_base.models import Turno
from usuarios.models import Usuario

import json

from django.db.models import Q, F, Value
from django.db.models.functions import Concat

from django.utils import timezone

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


# ============================================================================
# VIEWS PARA CHECKLISTS
# ============================================================================

@login_required
def lista_checklists(request):
    """Lista todos os checklists"""
    search = request.GET.get('search', '')
    checklists = Checklist.objects.select_related('ferramenta').all()

    if search:
        checklists = checklists.filter(nome__icontains=search)

    paginator = Paginator(checklists, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Checklists',
        'create_url': 'auditorias:criar_checklist'
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


@login_required
def editar_checklist(request, pk):
    """Edita um checklist existente, incluindo seus tópicos, perguntas e opções."""
    checklist = get_object_or_404(Checklist.objects.prefetch_related(
        'topicos__perguntas__opcoes_resposta',
        'topicos__perguntas__opcoes_porcentagem'
    ), pk=pk)

    if request.method == 'POST':
        try:
            # 1. ATUALIZAR DADOS DO CHECKLIST
            checklist.nome = request.POST.get('nome')
            checklist.ativo = request.POST.get('ativo') == 'on'
            ferramenta_id = request.POST.get('ferramenta')
            checklist.ferramenta_id = ferramenta_id if ferramenta_id else None
            checklist.save()

            # Processar estrutura completa
            processar_estrutura_checklist(request, checklist)

            messages.success(request, 'Checklist atualizado com sucesso!')
            return redirect('auditorias:lista_checklists')

        except Exception as e:
            messages.error(request, f'Erro ao atualizar checklist: {repr(e)}')
            import traceback
            print(traceback.format_exc())

    context = {
        'checklist': checklist,
        'object': checklist,
        'ferramentas': FerramentaDigital.objects.all(),
        'status_opcoes': OpcaoResposta._meta.get_field('status').choices,
        'title': 'Editar Checklist',
        'back_url': 'auditorias:lista_checklists'
    }
    return render(request, 'auditorias/checklists/form.html', context)


def processar_estrutura_checklist(request, checklist):
    """Processa e salva toda a estrutura de tópicos, perguntas e opções do checklist."""

    # Rastrear IDs processados para identificar o que deve ser deletado
    topicos_ids_processados = set()
    perguntas_ids_processadas = set()
    opcoes_resposta_ids_processadas = set()
    opcoes_porcentagem_ids_processadas = set()

    # Coletar todos os tópicos do POST
    topicos_data = {}
    for key in request.POST:
        if key.startswith('topico-descricao['):
            topico_id = key.split('[')[1].split(']')[0]
            topicos_data[topico_id] = {
                'descricao': request.POST.get(key),
                'ordem': request.POST.get(f'topico-ordem[{topico_id}]', 0)
            }

    print(f"Processando {len(topicos_data)} tópicos")

    # Processar cada tópico
    for topico_id_str, topico_info in topicos_data.items():
        # Criar ou atualizar tópico
        if topico_id_str.startswith('new-'):
            topico = Topico.objects.create(
                checklist=checklist,
                descricao=topico_info['descricao'],
                ordem=int(topico_info['ordem']) if topico_info['ordem'] else 0
            )
            print(f"Novo tópico criado: {topico.id}")
        else:
            try:
                topico = Topico.objects.get(
                    pk=int(topico_id_str), checklist=checklist)
                topico.descricao = topico_info['descricao']
                topico.ordem = int(
                    topico_info['ordem']) if topico_info['ordem'] else 0
                topico.save()
                print(f"Tópico atualizado: {topico.id}")
            except Topico.DoesNotExist:
                print(f"Tópico {topico_id_str} não encontrado, pulando...")
                continue

        topicos_ids_processados.add(topico.id)

        # Processar perguntas do tópico
        perguntas_data = {}
        for key in request.POST:
            if key.startswith(f'pergunta-descricao[{topico_id_str}-'):
                pergunta_id_full = key.split('[')[1].split(']')[0]
                pergunta_id = pergunta_id_full.replace(f'{topico_id_str}-', '')
                perguntas_data[pergunta_id] = {
                    'descricao': request.POST.get(key),
                    'ordem': request.POST.get(f'pergunta-ordem[{pergunta_id_full}]', 0),
                    'obrigatoria': request.POST.get(f'pergunta-obrigatorio[{pergunta_id_full}]') == 'on',
                    'resposta_livre': request.POST.get(f'pergunta-resposta_livre[{pergunta_id_full}]') == 'on',
                    'foto': request.POST.get(f'pergunta-foto[{pergunta_id_full}]') == 'on',
                    'criar_opcao': request.POST.get(f'pergunta-criar_opcao[{pergunta_id_full}]') == 'on',
                    'porcentagem': request.POST.get(f'pergunta-porcentagem[{pergunta_id_full}]') == 'on',
                    'id_full': pergunta_id_full
                }

        print(
            f"  Processando {len(perguntas_data)} perguntas do tópico {topico.id}")

        for pergunta_id_str, pergunta_info in perguntas_data.items():
            # Criar ou atualizar pergunta
            if pergunta_id_str.startswith('new-'):
                pergunta = Pergunta.objects.create(
                    topico=topico,
                    descricao=pergunta_info['descricao'],
                    ordem=int(pergunta_info['ordem']
                              ) if pergunta_info['ordem'] else 0,
                    obrigatoria=pergunta_info['obrigatoria'],
                    resposta_livre=pergunta_info['resposta_livre'],
                    foto=pergunta_info['foto'],
                    criar_opcao=pergunta_info['criar_opcao'],
                    porcentagem=pergunta_info['porcentagem']
                )
                print(f"    Nova pergunta criada: {pergunta.id}")
            else:
                try:
                    pergunta = Pergunta.objects.get(
                        pk=int(pergunta_id_str), topico=topico)
                    pergunta.descricao = pergunta_info['descricao']
                    pergunta.ordem = int(
                        pergunta_info['ordem']) if pergunta_info['ordem'] else 0
                    pergunta.obrigatoria = pergunta_info['obrigatoria']
                    pergunta.resposta_livre = pergunta_info['resposta_livre']
                    pergunta.foto = pergunta_info['foto']
                    pergunta.criar_opcao = pergunta_info['criar_opcao']
                    pergunta.porcentagem = pergunta_info['porcentagem']
                    pergunta.save()
                    print(f"    Pergunta atualizada: {pergunta.id}")
                except Pergunta.DoesNotExist:
                    print(
                        f"    Pergunta {pergunta_id_str} não encontrada, pulando...")
                    continue

            perguntas_ids_processadas.add(pergunta.id)

            # Processar opções de resposta
            if pergunta_info['criar_opcao']:
                opcoes_resposta_data = {}
                for key in request.POST:
                    if key.startswith(f'opcao-resposta-descricao[{pergunta_info["id_full"]}-'):
                        opcao_id_full = key.split('[')[1].split(']')[0]
                        opcao_id = opcao_id_full.replace(
                            f'{pergunta_info["id_full"]}-', '')
                        opcoes_resposta_data[opcao_id] = {
                            'descricao': request.POST.get(key),
                            'status': request.POST.get(f'opcao-resposta-status[{opcao_id_full}]', 'CONFORME')
                        }

                print(
                    f"      Processando {len(opcoes_resposta_data)} opções de resposta")

                for opcao_id_str, opcao_info in opcoes_resposta_data.items():
                    if opcao_id_str.startswith('new-'):
                        opcao = OpcaoResposta.objects.create(
                            pergunta=pergunta,
                            descricao=opcao_info['descricao'],
                            status=opcao_info['status']
                        )
                        print(
                            f"        Nova opção de resposta criada: {opcao.id}")
                    else:
                        try:
                            opcao = OpcaoResposta.objects.get(
                                pk=int(opcao_id_str), pergunta=pergunta)
                            opcao.descricao = opcao_info['descricao']
                            opcao.status = opcao_info['status']
                            opcao.save()
                            print(
                                f"        Opção de resposta atualizada: {opcao.id}")
                        except OpcaoResposta.DoesNotExist:
                            print(
                                f"        Opção de resposta {opcao_id_str} não encontrada")
                            continue

                    opcoes_resposta_ids_processadas.add(opcao.id)

            # Processar opções de porcentagem
            if pergunta_info['porcentagem']:
                opcoes_porcentagem_data = {}
                for key in request.POST:
                    if key.startswith(f'opcao-porcentagem-descricao[{pergunta_info["id_full"]}-'):
                        opcao_id_full = key.split('[')[1].split(']')[0]
                        opcao_id = opcao_id_full.replace(
                            f'{pergunta_info["id_full"]}-', '')
                        opcoes_porcentagem_data[opcao_id] = {
                            'descricao': request.POST.get(key),
                            'peso': request.POST.get(f'opcao-porcentagem-peso[{opcao_id_full}]', 0),
                            'cor': request.POST.get(f'opcao-porcentagem-cor[{opcao_id_full}]', '#FFFFFF')
                        }

                print(
                    f"      Processando {len(opcoes_porcentagem_data)} opções de porcentagem")

                for opcao_id_str, opcao_info in opcoes_porcentagem_data.items():
                    if opcao_id_str.startswith('new-'):
                        opcao = OpcaoPorcentagem.objects.create(
                            pergunta=pergunta,
                            descricao=opcao_info['descricao'],
                            peso=int(opcao_info['peso']
                                     ) if opcao_info['peso'] else 0,
                            cor=opcao_info['cor']
                        )
                        print(
                            f"        Nova opção de porcentagem criada: {opcao.id}")
                    else:
                        try:
                            opcao = OpcaoPorcentagem.objects.get(
                                pk=int(opcao_id_str), pergunta=pergunta)
                            opcao.descricao = opcao_info['descricao']
                            opcao.peso = int(
                                opcao_info['peso']) if opcao_info['peso'] else 0
                            opcao.cor = opcao_info['cor']
                            opcao.save()
                            print(
                                f"        Opção de porcentagem atualizada: {opcao.id}")
                        except OpcaoPorcentagem.DoesNotExist:
                            print(
                                f"        Opção de porcentagem {opcao_id_str} não encontrada")
                            continue

                    opcoes_porcentagem_ids_processadas.add(opcao.id)

    # Deletar itens que foram removidos do formulário
    print("\nRemovendo itens não processados...")

    # Deletar opções não processadas
    opcoes_resposta_deletadas = OpcaoResposta.objects.filter(
        pergunta__topico__checklist=checklist
    ).exclude(id__in=opcoes_resposta_ids_processadas).delete()
    print(f"Opções de resposta deletadas: {opcoes_resposta_deletadas}")

    opcoes_porcentagem_deletadas = OpcaoPorcentagem.objects.filter(
        pergunta__topico__checklist=checklist
    ).exclude(id__in=opcoes_porcentagem_ids_processadas).delete()
    print(f"Opções de porcentagem deletadas: {opcoes_porcentagem_deletadas}")

    # Deletar perguntas não processadas
    perguntas_deletadas = Pergunta.objects.filter(
        topico__checklist=checklist
    ).exclude(id__in=perguntas_ids_processadas).delete()
    print(f"Perguntas deletadas: {perguntas_deletadas}")

    # Deletar tópicos não processados
    topicos_deletados = Topico.objects.filter(
        checklist=checklist
    ).exclude(id__in=topicos_ids_processados).delete()
    print(f"Tópicos deletados: {topicos_deletados}")

    print(f"\nProcessamento concluído para checklist {checklist.id}")


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
        'button_text': 'Nova Auditoria',
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
            auditoria.local_area_id = request.POST.get('local_area') or None
            auditoria.local_setor_id = request.POST.get('local_setor') or None
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
            auditoria.contem_turnos = request.POST.get('contem_turnos') == 'on'

            # --- Salva TUDO de uma vez (isso também vai recriar as instâncias futuras) ---
            auditoria.save()

            # Atualiza as relações ManyToMany
            auditoria.modelos.set(request.POST.getlist('modelos'))
            auditoria.ativos_auditados.set(
                request.POST.getlist('ativos_auditados'))
            auditoria.turnos.set(request.POST.getlist('turnos'))

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
            auditoria_agendada__responsavel=user
        ).select_related(  # Otimiza a consulta ao banco de dados
            'auditoria_agendada__local_empresa',
            'auditoria_agendada__local_area',
            'auditoria_agendada__local_setor',
            'auditoria_agendada__local_subsetor'
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
        return AuditoriaInstancia.objects.filter(auditoria_agendada__responsavel=user)


class SubmeterAuditoriaAPIView(APIView):
    """
    Endpoint para submeter as respostas de uma instância de auditoria.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            instancia = AuditoriaInstancia.objects.get(
                pk=pk,
                auditoria_agendada__responsavel=request.user,
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
        'auditoria_agendada__criado_por',  # Adicionado
        'local_execucao'  # Adicionado
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

    # --- INÍCIO DA CORREÇÃO ---
    all_users_list = list(Usuario.objects.filter(is_active=True).annotate(
        name=Concat('first_name', Value(' '), 'last_name')
    ).values('id', 'name'))
    # --- FIM DA CORREÇÃO ---

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Auditorias para Execução',
        # Passa o JSON para o template
        'all_users_json': json.dumps(all_users_list)
    }
    return render(request, 'auditorias/execucoes.html', context)


@login_required
def historico_concluidas(request):
    """Exibe o histórico de todas as instâncias de auditoria CONCLUÍDAS."""

    # A query agora filtra apenas as instâncias executadas
    instancias_list = AuditoriaInstancia.objects.filter(executada=True).select_related(
        'auditoria_agendada__responsavel',
        'auditoria_agendada__criado_por',
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
        'title': 'Histórico de Auditorias Concluídas'
    }
    return render(request, 'auditorias/historico_concluidas.html', context)


@login_required
def redirecionar_agendamento(request, pk):
    """ Redireciona o auditor de um AGENDAMENTO PAI e de todas as suas execuções futuras. """
    agendamento = get_object_or_404(Auditoria, pk=pk)
    if request.method == 'POST':
        novo_responsavel_id = request.POST.get('responsavel_id')
        if novo_responsavel_id:
            try:
                # 1. Atualiza o responsável do agendamento pai
                agendamento.responsavel_id = novo_responsavel_id
                agendamento.save(update_fields=['responsavel'])

                # 2. Atualiza o responsável de todas as execuções filhas NÃO CONCLUÍDAS
                agendamento.instancias.filter(executada=False).update(
                    responsavel_id=novo_responsavel_id)

                messages.success(
                    request, f'Agendamento #{agendamento.id} e suas execuções foram redirecionados.')
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
