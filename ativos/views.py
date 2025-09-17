# ativos/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse

from .models import Categoria, Marca, Modelo, Ativo
from organizacao.models import SubSetor


# ============================================================================
# DASHBOARD
# ============================================================================

@login_required
def dashboard_ativos(request):
    """Dashboard principal do módulo de ativos"""
    context = {
        'total_ativos': Ativo.objects.count(),
        'ativos_ativos': Ativo.objects.filter(ativo=True).count(),
        'total_categorias': Categoria.objects.count(),
        'total_marcas': Marca.objects.count(),
        'total_modelos': Modelo.objects.count(),
        'ativos_recentes': Ativo.objects.select_related(
            'categoria', 'marca', 'modelo', 'estrutura_organizacional'
        ).order_by('-data_cadastro')[:5],
    }
    return render(request, 'ativos/dashboard.html', context)


# ============================================================================
# VIEWS PARA CATEGORIAS
# ============================================================================

@login_required
def lista_categorias(request):
    """Lista todas as categorias de ativos"""
    search = request.GET.get('search', '')
    categorias = Categoria.objects.annotate(
        total_ativos=Count('ativos_categoria')
    )
    
    if search:
        categorias = categorias.filter(
            Q(nome__icontains=search) | Q(descricao__icontains=search)
        )
    
    paginator = Paginator(categorias, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Categorias de Ativos',
        'singular': 'Categoria',
        'button_text': 'Nova Categoria',
        'create_url': 'ativos:criar_categoria',
        'artigo': 'a',
        'empty_message': 'Nenhuma categoria cadastrada',
        'empty_subtitle': 'Comece criando a primeira categoria.'
    }
    return render(request, 'ativos/categorias/lista.html', context)


@login_required
def criar_categoria(request):
    """Cria uma nova categoria"""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao', '')
        ativo = request.POST.get('ativo') == 'on'
        
        if nome:
            try:
                Categoria.objects.create(
                    nome=nome,
                    descricao=descricao,
                    ativo=ativo
                )
                messages.success(request, 'Categoria criada com sucesso!')
                return redirect('ativos:lista_categorias')
            except Exception as e:
                messages.error(request, f'Erro ao criar categoria: {str(e)}')
        else:
            messages.error(request, 'Nome é obrigatório!')
    
    context = {
        'title': 'Criar Categoria',
        'back_url': 'ativos:lista_categorias'
    }
    return render(request, 'ativos/categorias/form.html', context)


@login_required
def editar_categoria(request, pk):
    """Edita uma categoria existente"""
    categoria = get_object_or_404(Categoria, pk=pk)
    
    if request.method == 'POST':
        categoria.nome = request.POST.get('nome')
        categoria.descricao = request.POST.get('descricao', '')
        categoria.ativo = request.POST.get('ativo') == 'on'
        
        try:
            categoria.save()
            messages.success(request, 'Categoria atualizada com sucesso!')
            return redirect('ativos:lista_categorias')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar categoria: {str(e)}')
    
    context = {
        'categoria': categoria,
        'title': 'Editar Categoria',
        'back_url': 'ativos:lista_categorias'
    }
    return render(request, 'ativos/categorias/form.html', context)


@login_required
def deletar_categoria(request, pk):
    """Deleta uma categoria"""
    categoria = get_object_or_404(Categoria, pk=pk)
    
    if request.method == 'POST':
        try:
            categoria.delete()
            messages.success(request, 'Categoria deletada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar categoria: {str(e)}')
        return redirect('ativos:lista_categorias')
    
    context = {
        'object': categoria,
        'title': 'Categoria'
    }
    return render(request, 'auditorias/deletar_generico.html', context)


# ============================================================================
# VIEWS PARA MARCAS
# ============================================================================

@login_required
def lista_marcas(request):
    """Lista todas as marcas"""
    search = request.GET.get('search', '')
    marcas = Marca.objects.annotate(
        total_modelos=Count('modelo'),
        total_ativos=Count('ativos_marca')
    )
    
    if search:
        marcas = marcas.filter(nome__icontains=search)
    
    paginator = Paginator(marcas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Marcas',
        'singular': 'Marca',
        'button_text': 'Nova Marca',
        'create_url': 'ativos:criar_marca',
        'artigo': 'a',
        'empty_message': 'Nenhuma marca cadastrada',
        'empty_subtitle': 'Comece criando a primeira marca.'
    }
    return render(request, 'ativos/marcas/lista.html', context)


@login_required
def criar_marca(request):
    """Cria uma nova marca"""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        ativo = request.POST.get('ativo') == 'on'
        
        if nome:
            try:
                Marca.objects.create(
                    nome=nome,
                    ativo=ativo
                )
                messages.success(request, 'Marca criada com sucesso!')
                return redirect('ativos:lista_marcas')
            except Exception as e:
                messages.error(request, f'Erro ao criar marca: {str(e)}')
        else:
            messages.error(request, 'Nome é obrigatório!')
    
    context = {
        'title': 'Criar Marca',
        'back_url': 'ativos:lista_marcas'
    }
    return render(request, 'ativos/marcas/form.html', context)


@login_required
def editar_marca(request, pk):
    """Edita uma marca existente"""
    marca = get_object_or_404(Marca, pk=pk)
    
    if request.method == 'POST':
        marca.nome = request.POST.get('nome')
        marca.ativo = request.POST.get('ativo') == 'on'
        
        try:
            marca.save()
            messages.success(request, 'Marca atualizada com sucesso!')
            return redirect('ativos:lista_marcas')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar marca: {str(e)}')
    
    context = {
        'marca': marca,
        'title': 'Editar Marca',
        'back_url': 'ativos:lista_marcas'
    }
    return render(request, 'ativos/marcas/form.html', context)


@login_required
def deletar_marca(request, pk):
    """Deleta uma marca"""
    marca = get_object_or_404(Marca, pk=pk)
    
    if request.method == 'POST':
        try:
            marca.delete()
            messages.success(request, 'Marca deletada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar marca: {str(e)}')
        return redirect('ativos:lista_marcas')
    
    context = {
        'object': marca,
        'title': 'Marca'
    }
    return render(request, 'auditorias/deletar_generico.html', context)


# ============================================================================
# VIEWS PARA MODELOS
# ============================================================================

@login_required
def lista_modelos(request):
    """Lista todos os modelos"""
    search = request.GET.get('search', '')
    marca_filter = request.GET.get('marca', '')
    
    modelos = Modelo.objects.select_related('marca').annotate(
        total_ativos=Count('ativos_modelo')
    )
    
    if search:
        modelos = modelos.filter(
            Q(nome__icontains=search) | 
            Q(marca__nome__icontains=search) |
            Q(descricao__icontains=search)
        )
    
    if marca_filter:
        modelos = modelos.filter(marca_id=marca_filter)
    
    paginator = Paginator(modelos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'marca_filter': marca_filter,
        'marcas': Marca.objects.filter(ativo=True),
        'title': 'Modelos',
        'singular': 'Modelo',
        'button_text': 'Novo Modelo',
        'create_url': 'ativos:criar_modelo',
        'artigo': 'o',
        'empty_message': 'Nenhum modelo cadastrado',
        'empty_subtitle': 'Comece criando o primeiro modelo.'
    }
    return render(request, 'ativos/modelos/lista.html', context)


@login_required
def criar_modelo(request):
    """Cria um novo modelo"""
    if request.method == 'POST':
        marca_id = request.POST.get('marca')
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao', '')
        ativo = request.POST.get('ativo') == 'on'
        
        if marca_id and nome:
            try:
                marca = Marca.objects.get(pk=marca_id)
                Modelo.objects.create(
                    marca=marca,
                    nome=nome,
                    descricao=descricao,
                    ativo=ativo
                )
                messages.success(request, 'Modelo criado com sucesso!')
                return redirect('ativos:lista_modelos')
            except Exception as e:
                messages.error(request, f'Erro ao criar modelo: {str(e)}')
        else:
            messages.error(request, 'Marca e nome são obrigatórios!')
    
    context = {
        'marcas': Marca.objects.filter(ativo=True),
        'title': 'Criar Modelo',
        'back_url': 'ativos:lista_modelos'
    }
    return render(request, 'ativos/modelos/form.html', context)


@login_required
def editar_modelo(request, pk):
    """Edita um modelo existente"""
    modelo = get_object_or_404(Modelo, pk=pk)
    
    if request.method == 'POST':
        marca_id = request.POST.get('marca')
        modelo.nome = request.POST.get('nome')
        modelo.descricao = request.POST.get('descricao', '')
        modelo.ativo = request.POST.get('ativo') == 'on'
        
        if marca_id:
            modelo.marca = Marca.objects.get(pk=marca_id)
        
        try:
            modelo.save()
            messages.success(request, 'Modelo atualizado com sucesso!')
            return redirect('ativos:lista_modelos')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar modelo: {str(e)}')
    
    context = {
        'modelo': modelo,
        'marcas': Marca.objects.filter(ativo=True),
        'title': 'Editar Modelo',
        'back_url': 'ativos:lista_modelos'
    }
    return render(request, 'ativos/modelos/form.html', context)


@login_required
def deletar_modelo(request, pk):
    """Deleta um modelo"""
    modelo = get_object_or_404(Modelo, pk=pk)
    
    if request.method == 'POST':
        try:
            modelo.delete()
            messages.success(request, 'Modelo deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar modelo: {str(e)}')
        return redirect('ativos:lista_modelos')
    
    context = {
        'object': modelo,
        'title': 'Modelo'
    }
    return render(request, 'auditorias/deletar_generico.html', context)


# ============================================================================
# VIEWS PARA ATIVOS
# ============================================================================

@login_required
def lista_ativos(request):
    """Lista todos os ativos"""
    search = request.GET.get('search', '')
    categoria_filter = request.GET.get('categoria', '')
    marca_filter = request.GET.get('marca', '')
    
    ativos = Ativo.objects.select_related(
        'categoria', 'marca', 'modelo', 'estrutura_organizacional'
    )
    
    if search:
        ativos = ativos.filter(
            Q(tag__icontains=search) |
            Q(descricao__icontains=search) |
            Q(codigo_fabricante__icontains=search)
        )
    
    if categoria_filter:
        ativos = ativos.filter(categoria_id=categoria_filter)
    
    if marca_filter:
        ativos = ativos.filter(marca_id=marca_filter)
    
    paginator = Paginator(ativos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'categoria_filter': categoria_filter,
        'marca_filter': marca_filter,
        'categorias': Categoria.objects.filter(ativo=True),
        'marcas': Marca.objects.filter(ativo=True),
        'title': 'Ativos',
        'singular': 'Ativo',
        'button_text': 'Novo Ativo',
        'create_url': 'ativos:criar_ativo',
        'artigo': 'o',
        'empty_message': 'Nenhum ativo cadastrado',
        'empty_subtitle': 'Comece criando o primeiro ativo.'
    }
    return render(request, 'ativos/lista.html', context)


@login_required
def criar_ativo(request):
    """Cria um novo ativo"""
    if request.method == 'POST':
        tag = request.POST.get('tag')
        descricao = request.POST.get('descricao')
        custo = request.POST.get('custo') or None
        codigo_fabricante = request.POST.get('codigo_fabricante', '')
        categoria_id = request.POST.get('categoria') or None
        marca_id = request.POST.get('marca') or None
        modelo_id = request.POST.get('modelo') or None
        estrutura_id = request.POST.get('estrutura_organizacional') or None
        ativo = request.POST.get('ativo') == 'on'
        
        if tag and descricao:
            try:
                novo_ativo = Ativo.objects.create(
                    tag=tag,
                    descricao=descricao,
                    custo=custo,
                    codigo_fabricante=codigo_fabricante,
                    categoria_id=categoria_id,
                    marca_id=marca_id,
                    modelo_id=modelo_id,
                    estrutura_organizacional_id=estrutura_id,
                    ativo=ativo
                )
                
                # Processar imagem se fornecida
                if request.FILES.get('imagem_ativo'):
                    novo_ativo.imagem_ativo = request.FILES['imagem_ativo']
                    novo_ativo.save()
                
                messages.success(request, 'Ativo criado com sucesso!')
                return redirect('ativos:lista_ativos')
            except Exception as e:
                messages.error(request, f'Erro ao criar ativo: {str(e)}')
        else:
            messages.error(request, 'Tag e descrição são obrigatórios!')
    
    context = {
        'categorias': Categoria.objects.filter(ativo=True),
        'marcas': Marca.objects.filter(ativo=True),
        'modelos': Modelo.objects.filter(ativo=True),
        'subsetores': SubSetor.objects.filter(ativo=True),
        'title': 'Criar Ativo',
        'back_url': 'ativos:lista_ativos'
    }
    return render(request, 'ativos/ativos/form.html', context)


@login_required
def editar_ativo(request, pk):
    """Edita um ativo existente"""
    ativo_obj = get_object_or_404(Ativo, pk=pk)
    
    if request.method == 'POST':
        ativo_obj.tag = request.POST.get('tag')
        ativo_obj.descricao = request.POST.get('descricao')
        ativo_obj.custo = request.POST.get('custo') or None
        ativo_obj.codigo_fabricante = request.POST.get('codigo_fabricante', '')
        ativo_obj.categoria_id = request.POST.get('categoria') or None
        ativo_obj.marca_id = request.POST.get('marca') or None
        ativo_obj.modelo_id = request.POST.get('modelo') or None
        ativo_obj.estrutura_organizacional_id = request.POST.get('estrutura_organizacional') or None
        ativo_obj.ativo = request.POST.get('ativo') == 'on'
        
        try:
            # Processar imagem se fornecida
            if request.FILES.get('imagem_ativo'):
                ativo_obj.imagem_ativo = request.FILES['imagem_ativo']
            
            ativo_obj.save()
            messages.success(request, 'Ativo atualizado com sucesso!')
            return redirect('ativos:lista_ativos')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar ativo: {str(e)}')
    
    context = {
        'ativo': ativo_obj,
        'categorias': Categoria.objects.filter(ativo=True),
        'marcas': Marca.objects.filter(ativo=True),
        'modelos': Modelo.objects.filter(ativo=True),
        'subsetores': SubSetor.objects.filter(ativo=True),
        'title': 'Editar Ativo',
        'back_url': 'ativos:lista_ativos'
    }
    return render(request, 'ativos/ativos/form.html', context)


@login_required
def deletar_ativo(request, pk):
    """Deleta um ativo"""
    ativo = get_object_or_404(Ativo, pk=pk)
    
    if request.method == 'POST':
        try:
            ativo.delete()
            messages.success(request, 'Ativo deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar ativo: {str(e)}')
        return redirect('ativos:lista_ativos')
    
    context = {
        'object': ativo,
        'title': 'Ativo'
    }
    return render(request, 'auditorias/deletar_generico.html', context)


# ============================================================================
# VIEWS AJAX
# ============================================================================

@login_required
def get_modelos_por_marca(request):
    """Retorna modelos de uma marca via AJAX"""
    marca_id = request.GET.get('marca_id')
    modelos = Modelo.objects.filter(marca_id=marca_id, ativo=True).values('id', 'nome')
    return JsonResponse(list(modelos), safe=False)