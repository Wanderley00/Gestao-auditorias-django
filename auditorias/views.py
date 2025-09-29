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

from .models import (
    Pilar, CategoriaAuditoria, Norma, RequisitoNorma, FerramentaDigital,
    Checklist, Topico, Pergunta, OpcaoResposta, OpcaoPorcentagem,
    FerramentaCausaRaiz, ModeloAuditoria, Auditoria, AuditoriaInstancia
)
from organizacao.models import Empresa, Area, Setor, SubSetor
from ativos.models import Ativo
from cadastros_base.models import Turno
from usuarios.models import Usuario


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
                messages.error(request, f'Erro ao criar pilar: {str(e)}')
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
            messages.error(request, f'Erro ao atualizar pilar: {str(e)}')
    
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
            messages.error(request, f'Erro ao deletar pilar: {str(e)}')
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
                messages.error(request, f'Erro ao criar categoria: {str(e)}')
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
            messages.error(request, f'Erro ao atualizar categoria: {str(e)}')
    
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
            messages.error(request, f'Erro ao deletar categoria: {str(e)}')
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
                messages.error(request, f'Erro ao criar norma: {str(e)}')
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
            messages.error(request, f'Erro ao atualizar norma: {str(e)}')
    
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
            messages.error(request, f'Erro ao deletar norma: {str(e)}')
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
                messages.success(request, 'Ferramenta digital criada com sucesso!')
                return redirect('auditorias:lista_ferramentas_digitais')
            except Exception as e:
                messages.error(request, f'Erro ao criar ferramenta: {str(e)}')
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
            messages.success(request, 'Ferramenta digital atualizada com sucesso!')
            return redirect('auditorias:lista_ferramentas_digitais')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar ferramenta: {str(e)}')
    
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
            messages.success(request, 'Ferramenta digital deletada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar ferramenta: {str(e)}')
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
    """Cria um novo checklist e redireciona para a tela de edição detalhada."""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        ferramenta_id = request.POST.get('ferramenta')
        ativo = request.POST.get('ativo') == 'on'
        
        if nome:
            try:
                checklist = Checklist.objects.create(
                    nome=nome,
                    ativo=ativo
                )
                
                if ferramenta_id:
                    checklist.ferramenta = FerramentaDigital.objects.get(pk=ferramenta_id)
                
                checklist.save()
                messages.success(request, 'Checklist criado com sucesso! Agora adicione os tópicos e perguntas.')
                return redirect('auditorias:editar_checklist', pk=checklist.pk)
            except Exception as e:
                messages.error(request, f'Erro ao criar checklist: {str(e)}')
        else:
            messages.error(request, 'Nome é obrigatório!')
    
    context = {
        'ferramentas': FerramentaDigital.objects.all(),
        'title': 'Criar Checklist',
        'back_url': 'auditorias:lista_checklists'
    }
    return render(request, 'auditorias/checklists/form.html', context)

@login_required
def editar_checklist(request, pk):
    """Edita um checklist existente, incluindo seus tópicos, perguntas e opções em uma única tela."""
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

            # IDs de itens que foram enviados no formulário (para saber quais deletar)
            topicos_ids_enviados = []
            perguntas_ids_enviadas = []
            opcoes_resposta_ids_enviadas = []
            opcoes_porcentagem_ids_enviadas = []

            # 2. PROCESSAR TÓPICOS
            for key, descricao in request.POST.items():
                if not key.startswith('topico-descricao['):
                    continue
                
                id_str = key.split('[')[1].split(']')[0]
                ordem = request.POST.get(f'topico-ordem[{id_str}]', 0)
                
                if id_str.startswith('new-'):
                    topico = Topico.objects.create(checklist=checklist, descricao=descricao, ordem=ordem)
                else:
                    topico = get_object_or_404(Topico, pk=int(id_str), checklist=checklist)
                    topico.descricao, topico.ordem = descricao, ordem
                    topico.save()
                
                topicos_ids_enviados.append(topico.id)

                # 3. PROCESSAR PERGUNTAS DO TÓPICO
                for p_key, p_descricao in request.POST.items():
                    if not p_key.startswith(f'pergunta-descricao[{id_str}-'):
                        continue

                    p_id_str_full = p_key.split('[')[1].split(']')[0]
                    p_id_str = p_id_str_full.replace(f'{id_str}-', '')
                    
                    p_ordem = request.POST.get(f'pergunta-ordem[{p_id_str_full}]', 0)
                    p_obrigatorio = request.POST.get(f'pergunta-obrigatorio[{p_id_str_full}]') == 'on'
                    
                    # Capturar os tipos de resposta
                    p_resposta_livre = request.POST.get(f'pergunta-resposta_livre[{p_id_str_full}]') == 'on'
                    p_foto = request.POST.get(f'pergunta-foto[{p_id_str_full}]') == 'on'
                    p_criar_opcao = request.POST.get(f'pergunta-criar_opcao[{p_id_str_full}]') == 'on'
                    p_porcentagem = request.POST.get(f'pergunta-porcentagem[{p_id_str_full}]') == 'on'

                    if p_id_str.startswith('new-'):
                        pergunta = Pergunta.objects.create(
                            topico=topico, descricao=p_descricao,
                            ordem=p_ordem, obrigatoria=p_obrigatorio,
                            resposta_livre=p_resposta_livre, foto=p_foto,
                            criar_opcao=p_criar_opcao, porcentagem=p_porcentagem
                        )
                    else:
                        pergunta = get_object_or_404(Pergunta, pk=int(p_id_str), topico=topico)
                        pergunta.descricao = p_descricao
                        pergunta.ordem, pergunta.obrigatoria = p_ordem, p_obrigatorio
                        pergunta.resposta_livre, pergunta.foto = p_resposta_livre, p_foto
                        pergunta.criar_opcao, pergunta.porcentagem = p_criar_opcao, p_porcentagem
                        pergunta.save()
                    
                    perguntas_ids_enviadas.append(pergunta.id)

                    # 4. PROCESSAR OPÇÕES DE RESPOSTA
                    for or_key, or_descricao in request.POST.items():
                        if not or_key.startswith(f'opcao-resposta-descricao[{p_id_str_full}-'):
                            continue
                        
                        or_id_str_full = or_key.split('[')[1].split(']')[0]
                        or_id_str = or_id_str_full.replace(f'{p_id_str_full}-', '')

                        or_status = request.POST.get(f'opcao-resposta-status[{or_id_str_full}]')
                        
                        if or_id_str.startswith('new-'):
                            opcao_resposta = OpcaoResposta.objects.create(
                                pergunta=pergunta, descricao=or_descricao, status=or_status
                            )
                        else:
                            opcao_resposta = get_object_or_404(OpcaoResposta, pk=int(or_id_str), pergunta=pergunta)
                            opcao_resposta.descricao, opcao_resposta.status = or_descricao, or_status
                            opcao_resposta.save()
                        
                        opcoes_resposta_ids_enviadas.append(opcao_resposta.id)

                    # 5. PROCESSAR OPÇÕES DE PORCENTAGEM
                    for op_key, op_descricao in request.POST.items():
                        if not op_key.startswith(f'opcao-porcentagem-descricao[{p_id_str_full}-'):
                            continue
                        
                        op_id_str_full = op_key.split('[')[1].split(']')[0]
                        op_id_str = op_id_str_full.replace(f'{p_id_str_full}-', '')

                        op_peso = request.POST.get(f'opcao-porcentagem-peso[{op_id_str_full}]')
                        op_cor = request.POST.get(f'opcao-porcentagem-cor[{op_id_str_full}]')
                        
                        if op_id_str.startswith('new-'):
                            opcao_porcentagem = OpcaoPorcentagem.objects.create(
                                pergunta=pergunta, descricao=op_descricao, peso=op_peso, cor=op_cor
                            )
                        else:
                            opcao_porcentagem = get_object_or_404(OpcaoPorcentagem, pk=int(op_id_str), pergunta=pergunta)
                            opcao_porcentagem.descricao, opcao_porcentagem.peso, opcao_porcentagem.cor = op_descricao, op_peso, op_cor
                            opcao_porcentagem.save()
                        
                        opcoes_porcentagem_ids_enviadas.append(opcao_porcentagem.id)

            # 6. DELETAR ITENS QUE NÃO ESTAVAM NO FORMULÁRIO
            OpcaoResposta.objects.filter(pergunta__topico__checklist=checklist).exclude(id__in=opcoes_resposta_ids_enviadas).delete()
            OpcaoPorcentagem.objects.filter(pergunta__topico__checklist=checklist).exclude(id__in=opcoes_porcentagem_ids_enviadas).delete()
            Pergunta.objects.filter(topico__checklist=checklist).exclude(id__in=perguntas_ids_enviadas).delete()
            Topico.objects.filter(checklist=checklist).exclude(id__in=topicos_ids_enviados).delete()

            messages.success(request, 'Checklist atualizado com sucesso!')
            return redirect('auditorias:lista_checklists')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar checklist: {str(e)}')

    context = {
        'checklist': checklist,
        'object': checklist, # Para compatibilidade com o form_generico
        'ferramentas': FerramentaDigital.objects.all(),
        'status_opcoes': OpcaoResposta._meta.get_field('status').choices,
        'title': 'Editar Checklist',
        'back_url': 'auditorias:lista_checklists'
    }
    return render(request, 'auditorias/checklists/form.html', context)


@login_required
def deletar_checklist(request, pk):
    """Deleta um checklist"""
    checklist = get_object_or_404(Checklist, pk=pk)
    
    if request.method == 'POST':
        try:
            checklist.delete()
            messages.success(request, 'Checklist deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar checklist: {str(e)}')
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
    modelos = ModeloAuditoria.objects.select_related('checklist', 'categoria', 'ferramenta_causa_raiz').all()
    
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
        iniciar_por_codigo_qr = request.POST.get('iniciar_por_codigo_qr') == 'on'
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
                    modelo.categoria = CategoriaAuditoria.objects.get(pk=categoria_id)
                if ferramenta_causa_raiz_id:
                    modelo.ferramenta_causa_raiz = FerramentaCausaRaiz.objects.get(pk=ferramenta_causa_raiz_id)
                
                modelo.save()
                messages.success(request, 'Modelo de auditoria criado com sucesso!')
                return redirect('auditorias:lista_modelos_auditoria')
            except Exception as e:
                messages.error(request, f'Erro ao criar modelo: {str(e)}')
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
        modelo.iniciar_por_codigo_qr = request.POST.get('iniciar_por_codigo_qr') == 'on'
        
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
            modelo.ferramenta_causa_raiz = FerramentaCausaRaiz.objects.get(pk=ferramenta_causa_raiz_id)
        else:
            modelo.ferramenta_causa_raiz = None
        
        try:
            modelo.save()
            messages.success(request, 'Modelo de auditoria atualizado com sucesso!')
            return redirect('auditorias:lista_modelos_auditoria')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar modelo: {str(e)}')
    
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
            messages.success(request, 'Modelo de auditoria deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar modelo: {str(e)}')
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
    auditorias = Auditoria.objects.select_related('responsavel', 'ferramenta').prefetch_related('modelos').all()
    
    if search:
        auditorias = auditorias.filter(
            Q(responsavel__first_name__icontains=search) |
            Q(responsavel__last_name__icontains=search) |
            Q(ferramenta__nome__icontains=search)
        )
    
    paginator = Paginator(auditorias, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Auditorias Agendadas',
        'singular': 'Auditoria',
        'button_text': 'Nova Auditoria',
        'create_url': 'auditorias:criar_auditoria',
        'artigo': 'a',
        'empty_message': 'Nenhuma auditoria agendada',
        'empty_subtitle': 'Comece criando a primeira auditoria.'
    }
    return render(request, 'auditorias/auditorias/lista.html', context)

@login_required
def criar_auditoria(request):
    """Cria uma nova auditoria agendada"""
    if request.method == 'POST':
        # Dados básicos
        ferramenta_id = request.POST.get('ferramenta')
        responsavel_id = request.POST.get('responsavel')
        nivel_organizacional = request.POST.get('nivel_organizacional')
        categoria_auditoria = request.POST.get('categoria_auditoria')
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        
        # Dados de programação
        por_frequencia = request.POST.get('por_frequencia') == 'on'
        por_intervalo = request.POST.get('por_intervalo') == 'on'
        frequencia = request.POST.get('frequencia')
        intervalo = request.POST.get('intervalo')
        numero_repeticoes = request.POST.get('numero_repeticoes')
        pular_finais_semana = request.POST.get('pular_finais_semana') == 'on'
        contem_turnos = request.POST.get('contem_turnos') == 'on'
        
        # Locais organizacionais
        local_empresa_id = request.POST.get('local_empresa')
        local_area_id = request.POST.get('local_area')
        local_setor_id = request.POST.get('local_setor')
        local_subsetor_id = request.POST.get('local_subsetor')
        
        # Modelos e ativos
        modelos_ids = request.POST.getlist('modelos')
        ativos_ids = request.POST.getlist('ativos_auditados')
        turnos_ids = request.POST.getlist('turnos')
        
        if ferramenta_id and responsavel_id and nivel_organizacional and data_inicio:
            try:
                auditoria = Auditoria.objects.create(
                    ferramenta=FerramentaDigital.objects.get(pk=ferramenta_id),
                    responsavel=Usuario.objects.get(pk=responsavel_id),
                    nivel_organizacional=nivel_organizacional,
                    categoria_auditoria=categoria_auditoria,
                    data_inicio=data_inicio,
                    data_fim=data_fim if data_fim else None,
                    por_frequencia=por_frequencia,
                    por_intervalo=por_intervalo,
                    frequencia=frequencia if frequencia else None,
                    intervalo=int(intervalo) if intervalo else None,
                    numero_repeticoes=int(numero_repeticoes) if numero_repeticoes else None,
                    pular_finais_semana=pular_finais_semana,
                    contem_turnos=contem_turnos
                )
                
                # Definir locais organizacionais
                if local_empresa_id:
                    auditoria.local_empresa = Empresa.objects.get(pk=local_empresa_id)
                if local_area_id:
                    auditoria.local_area = Area.objects.get(pk=local_area_id)
                if local_setor_id:
                    auditoria.local_setor = Setor.objects.get(pk=local_setor_id)
                if local_subsetor_id:
                    auditoria.local_subsetor = SubSetor.objects.get(pk=local_subsetor_id)
                
                auditoria.save()
                
                # Adicionar modelos e ativos
                if modelos_ids:
                    auditoria.modelos.set(modelos_ids)
                if ativos_ids:
                    auditoria.ativos_auditados.set(ativos_ids)
                if turnos_ids:
                    auditoria.turnos.set(turnos_ids)
                
                messages.success(request, 'Auditoria criada com sucesso!')
                return redirect('auditorias:lista_auditorias')
            except Exception as e:
                messages.error(request, f'Erro ao criar auditoria: {str(e)}')
        else:
            messages.error(request, 'Campos obrigatórios não preenchidos!')
    
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
        # Atualizar dados básicos
        ferramenta_id = request.POST.get('ferramenta')
        responsavel_id = request.POST.get('responsavel')
        
        auditoria.nivel_organizacional = request.POST.get('nivel_organizacional')
        auditoria.categoria_auditoria = request.POST.get('categoria_auditoria')
        auditoria.data_inicio = request.POST.get('data_inicio')
        auditoria.data_fim = request.POST.get('data_fim') if request.POST.get('data_fim') else None
        
        # Dados de programação
        auditoria.por_frequencia = request.POST.get('por_frequencia') == 'on'
        auditoria.por_intervalo = request.POST.get('por_intervalo') == 'on'
        auditoria.frequencia = request.POST.get('frequencia') if request.POST.get('frequencia') else None
        auditoria.intervalo = int(request.POST.get('intervalo')) if request.POST.get('intervalo') else None
        auditoria.numero_repeticoes = int(request.POST.get('numero_repeticoes')) if request.POST.get('numero_repeticoes') else None
        auditoria.pular_finais_semana = request.POST.get('pular_finais_semana') == 'on'
        auditoria.contem_turnos = request.POST.get('contem_turnos') == 'on'
        
        if ferramenta_id:
            auditoria.ferramenta = FerramentaDigital.objects.get(pk=ferramenta_id)
        if responsavel_id:
            auditoria.responsavel = Usuario.objects.get(pk=responsavel_id)
        
        # Locais organizacionais
        local_empresa_id = request.POST.get('local_empresa')
        local_area_id = request.POST.get('local_area')
        local_setor_id = request.POST.get('local_setor')
        local_subsetor_id = request.POST.get('local_subsetor')
        
        auditoria.local_empresa = Empresa.objects.get(pk=local_empresa_id) if local_empresa_id else None
        auditoria.local_area = Area.objects.get(pk=local_area_id) if local_area_id else None
        auditoria.local_setor = Setor.objects.get(pk=local_setor_id) if local_setor_id else None
        auditoria.local_subsetor = SubSetor.objects.get(pk=local_subsetor_id) if local_subsetor_id else None
        
        try:
            auditoria.save()
            
            # Atualizar modelos e ativos
            modelos_ids = request.POST.getlist('modelos')
            ativos_ids = request.POST.getlist('ativos_auditados')
            turnos_ids = request.POST.getlist('turnos')
            
            auditoria.modelos.set(modelos_ids)
            auditoria.ativos_auditados.set(ativos_ids)
            auditoria.turnos.set(turnos_ids)
            
            messages.success(request, 'Auditoria atualizada com sucesso!')
            return redirect('auditorias:lista_auditorias')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar auditoria: {str(e)}')
    
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
            messages.error(request, f'Erro ao deletar auditoria: {str(e)}')
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
    areas = Area.objects.filter(empresa_id=empresa_id, ativo=True).values('id', 'nome')
    return JsonResponse(list(areas), safe=False)


@login_required
def get_setores_por_area(request):
    """Retorna setores de uma área via AJAX"""
    area_id = request.GET.get('area_id')
    setores = Setor.objects.filter(area_id=area_id, ativo=True).values('id', 'nome')
    return JsonResponse(list(setores), safe=False)


@login_required
def get_subsetores_por_setor(request):
    """Retorna subsetores de um setor via AJAX"""
    setor_id = request.GET.get('setor_id')
    subsetores = SubSetor.objects.filter(setor_id=setor_id, ativo=True).values('id', 'nome')
    return JsonResponse(list(subsetores), safe=False)


@login_required
def get_ativos_por_local(request):
    """Retorna ativos filtrados por localização via AJAX"""
    nivel = request.GET.get('nivel')
    local_id = request.GET.get('local_id')
    
    ativos = Ativo.objects.filter(ativo=True)
    
    if nivel == 'EMPRESA' and local_id:
        ativos = ativos.filter(estrutura_organizacional__setor__area__empresa_id=local_id)
    elif nivel == 'AREA' and local_id:
        ativos = ativos.filter(estrutura_organizacional__setor__area_id=local_id)
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
    topicos_com_perguntas = checklist.topicos.prefetch_related('perguntas').order_by('ordem')

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
                    campo_obrigatorio=request.POST.get('campo_obrigatorio') == 'on',
                    campo_desabilitado=request.POST.get('campo_desabilitado') == 'on',
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
    pergunta = get_object_or_404(Pergunta.objects.select_related('topico__checklist').prefetch_related('opcoes_resposta', 'opcoes_porcentagem'), pk=pk)
    checklist = pergunta.topico.checklist

    if request.method == 'POST':
        topico_id = request.POST.get('topico')
        descricao = request.POST.get('descricao')

        if topico_id and descricao:
            try:
                pergunta.topico_id = topico_id
                pergunta.descricao = descricao
                pergunta.campo_obrigatorio = request.POST.get('campo_obrigatorio') == 'on'
                pergunta.campo_desabilitado = request.POST.get('campo_desabilitado') == 'on'
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
    pergunta = get_object_or_404(Pergunta.objects.select_related('topico__checklist'), pk=pk)
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
    topicos = Topico.objects.select_related('checklist').order_by('checklist__nome', 'ordem')

    if search:
        topicos = topicos.filter(
            Q(descricao__icontains=search) | Q(checklist__nome__icontains=search)
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