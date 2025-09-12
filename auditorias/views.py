# auditorias/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .models import (
    Pilar, CategoriaAuditoria, Norma, RequisitoNorma, FerramentaDigital,
    TipoQuestao, ModeloAvaliacao, Checklist, Topico, Pergunta, OpcaoPergunta,
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
        'create_url': 'auditorias:criar_pilar'
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
    
    return render(request, 'auditorias/pilares/form.html', {'title': 'Criar Pilar'})


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
        'title': 'Editar Pilar'
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
# VIEWS PARA CATEGORIAS DE AUDITORIA
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
        'create_url': 'auditorias:criar_categoria_auditoria'
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
        'title': 'Criar Categoria de Auditoria'
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
        'title': 'Editar Categoria de Auditoria'
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
        'create_url': 'auditorias:criar_norma'
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
    
    return render(request, 'auditorias/normas/form.html', {'title': 'Criar Norma'})


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
        'title': 'Editar Norma'
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
        'create_url': 'auditorias:criar_ferramenta_digital'
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
    
    return render(request, 'auditorias/ferramentas_digitais/form.html', {'title': 'Criar Ferramenta Digital'})


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
        'title': 'Editar Ferramenta Digital'
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
# VIEWS PARA TIPOS DE QUESTÃO
# ============================================================================

@login_required
def lista_tipos_questao(request):
    """Lista todos os tipos de questão"""
    search = request.GET.get('search', '')
    tipos = TipoQuestao.objects.all()
    
    if search:
        tipos = tipos.filter(
            Q(nome__icontains=search) | Q(descricao__icontains=search)
        )
    
    paginator = Paginator(tipos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Tipos de Questão',
        'create_url': 'auditorias:criar_tipo_questao'
    }
    return render(request, 'auditorias/tipos_questao/lista.html', context)


@login_required
def criar_tipo_questao(request):
    """Cria um novo tipo de questão"""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        icone = request.FILES.get('icone')
        
        if nome and descricao:
            try:
                TipoQuestao.objects.create(
                    nome=nome,
                    descricao=descricao,
                    icone=icone
                )
                messages.success(request, 'Tipo de questão criado com sucesso!')
                return redirect('auditorias:lista_tipos_questao')
            except Exception as e:
                messages.error(request, f'Erro ao criar tipo de questão: {str(e)}')
        else:
            messages.error(request, 'Nome e descrição são obrigatórios!')
    
    return render(request, 'auditorias/tipos_questao/form.html', {'title': 'Criar Tipo de Questão'})


@login_required
def editar_tipo_questao(request, pk):
    """Edita um tipo de questão existente"""
    tipo = get_object_or_404(TipoQuestao, pk=pk)
    
    if request.method == 'POST':
        tipo.nome = request.POST.get('nome')
        tipo.descricao = request.POST.get('descricao')
        
        if request.FILES.get('icone'):
            tipo.icone = request.FILES.get('icone')
        
        try:
            tipo.save()
            messages.success(request, 'Tipo de questão atualizado com sucesso!')
            return redirect('auditorias:lista_tipos_questao')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar tipo de questão: {str(e)}')
    
    context = {
        'tipo': tipo,
        'title': 'Editar Tipo de Questão'
    }
    return render(request, 'auditorias/tipos_questao/form.html', context)


@login_required
def deletar_tipo_questao(request, pk):
    """Deleta um tipo de questão"""
    tipo = get_object_or_404(TipoQuestao, pk=pk)
    
    if request.method == 'POST':
        try:
            tipo.delete()
            messages.success(request, 'Tipo de questão deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar tipo de questão: {str(e)}')
        return redirect('auditorias:lista_tipos_questao')
    
    context = {
        'object': tipo,
        'title': 'Tipo de Questão'
    }
    return render(request, 'auditorias/deletar_generico.html', context)


# ============================================================================
# VIEWS PARA MODELOS DE AVALIAÇÃO
# ============================================================================

@login_required
def lista_modelos_avaliacao(request):
    """Lista todos os modelos de avaliação"""
    search = request.GET.get('search', '')
    modelos = ModeloAvaliacao.objects.prefetch_related('tipos_questao_suportados').all()
    
    if search:
        modelos = modelos.filter(
            Q(nome__icontains=search) | Q(descricao__icontains=search)
        )
    
    paginator = Paginator(modelos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Modelos de Avaliação',
        'create_url': 'auditorias:criar_modelo_avaliacao'
    }
    return render(request, 'auditorias/modelos_avaliacao/lista.html', context)


@login_required
def criar_modelo_avaliacao(request):
    """Cria um novo modelo de avaliação"""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        tipos_questao_ids = request.POST.getlist('tipos_questao_suportados')
        
        if nome and descricao:
            try:
                modelo = ModeloAvaliacao.objects.create(
                    nome=nome,
                    descricao=descricao
                )
                if tipos_questao_ids:
                    modelo.tipos_questao_suportados.set(tipos_questao_ids)
                
                messages.success(request, 'Modelo de avaliação criado com sucesso!')
                return redirect('auditorias:lista_modelos_avaliacao')
            except Exception as e:
                messages.error(request, f'Erro ao criar modelo: {str(e)}')
        else:
            messages.error(request, 'Nome e descrição são obrigatórios!')
    
    context = {
        'tipos_questao': TipoQuestao.objects.all(),
        'title': 'Criar Modelo de Avaliação'
    }
    return render(request, 'auditorias/modelos_avaliacao/form.html', context)


@login_required
def editar_modelo_avaliacao(request, pk):
    """Edita um modelo de avaliação existente"""
    modelo = get_object_or_404(ModeloAvaliacao, pk=pk)
    
    if request.method == 'POST':
        modelo.nome = request.POST.get('nome')
        modelo.descricao = request.POST.get('descricao')
        tipos_questao_ids = request.POST.getlist('tipos_questao_suportados')
        
        try:
            modelo.save()
            modelo.tipos_questao_suportados.set(tipos_questao_ids)
            messages.success(request, 'Modelo de avaliação atualizado com sucesso!')
            return redirect('auditorias:lista_modelos_avaliacao')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar modelo: {str(e)}')
    
    context = {
        'modelo': modelo,
        'tipos_questao': TipoQuestao.objects.all(),
        'title': 'Editar Modelo de Avaliação'
    }
    return render(request, 'auditorias/modelos_avaliacao/form.html', context)


@login_required
def deletar_modelo_avaliacao(request, pk):
    """Deleta um modelo de avaliação"""
    modelo = get_object_or_404(ModeloAvaliacao, pk=pk)
    
    if request.method == 'POST':
        try:
            modelo.delete()
            messages.success(request, 'Modelo de avaliação deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar modelo: {str(e)}')
        return redirect('auditorias:lista_modelos_avaliacao')
    
    context = {
        'object': modelo,
        'title': 'Modelo de Avaliação'
    }
    return render(request, 'auditorias/deletar_generico.html', context)


# ============================================================================
# VIEWS PARA CHECKLISTS
# ============================================================================

@login_required
def lista_checklists(request):
    """Lista todos os checklists"""
    search = request.GET.get('search', '')
    checklists = Checklist.objects.select_related('ferramenta', 'modelo_avaliacao').all()
    
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
    """Cria um novo checklist"""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        ferramenta_id = request.POST.get('ferramenta')
        modelo_avaliacao_id = request.POST.get('modelo_avaliacao')
        ativo = request.POST.get('ativo') == 'on'
        
        if nome:
            try:
                checklist = Checklist.objects.create(
                    nome=nome,
                    ativo=ativo
                )
                
                if ferramenta_id:
                    checklist.ferramenta = FerramentaDigital.objects.get(pk=ferramenta_id)
                if modelo_avaliacao_id:
                    checklist.modelo_avaliacao = ModeloAvaliacao.objects.get(pk=modelo_avaliacao_id)
                
                checklist.save()
                messages.success(request, 'Checklist criado com sucesso!')
                return redirect('auditorias:lista_checklists')
            except Exception as e:
                messages.error(request, f'Erro ao criar checklist: {str(e)}')
        else:
            messages.error(request, 'Nome é obrigatório!')
    
    context = {
        'ferramentas': FerramentaDigital.objects.all(),
        'modelos_avaliacao': ModeloAvaliacao.objects.all(),
        'title': 'Criar Checklist'
    }
    return render(request, 'auditorias/checklists/form.html', context)


@login_required
def editar_checklist(request, pk):
    """Edita um checklist existente"""
    checklist = get_object_or_404(Checklist, pk=pk)
    
    if request.method == 'POST':
        checklist.nome = request.POST.get('nome')
        checklist.ativo = request.POST.get('ativo') == 'on'
        
        ferramenta_id = request.POST.get('ferramenta')
        modelo_avaliacao_id = request.POST.get('modelo_avaliacao')
        
        if ferramenta_id:
            checklist.ferramenta = FerramentaDigital.objects.get(pk=ferramenta_id)
        else:
            checklist.ferramenta = None
            
        if modelo_avaliacao_id:
            checklist.modelo_avaliacao = ModeloAvaliacao.objects.get(pk=modelo_avaliacao_id)
        else:
            checklist.modelo_avaliacao = None
        
        try:
            checklist.save()
            messages.success(request, 'Checklist atualizado com sucesso!')
            return redirect('auditorias:lista_checklists')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar checklist: {str(e)}')
    
    context = {
        'checklist': checklist,
        'ferramentas': FerramentaDigital.objects.all(),
        'modelos_avaliacao': ModeloAvaliacao.objects.all(),
        'title': 'Editar Checklist'
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
        'create_url': 'auditorias:criar_modelo_auditoria'
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
        'title': 'Criar Modelo de Auditoria'
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
        'title': 'Editar Modelo de Auditoria'
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
        'create_url': 'auditorias:criar_auditoria'
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
        'title': 'Criar Auditoria'
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
        'title': 'Editar Auditoria'
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

