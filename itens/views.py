# itens/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse

from .models import Item, CategoriaItem, SubcategoriaItem, Almoxarifado
from cadastros_base.models import UnidadeMedida

# ============================================================================
# DASHBOARD
# ============================================================================

@login_required
def dashboard_itens(request):
    """Dashboard principal do módulo de itens."""
    context = {
        'total_itens': Item.objects.count(),
        'itens_ativos': Item.objects.filter(ativo=True).count(),
        'total_categorias': CategoriaItem.objects.count(),
        'total_subcategorias': SubcategoriaItem.objects.count(),
        'total_almoxarifados': Almoxarifado.objects.count(),
        'itens_recentes': Item.objects.select_related(
            'categoria_principal', 'almoxarifado'
        ).order_by('-data_cadastro')[:5],
    }
    return render(request, 'itens/dashboard.html', context)


# ============================================================================
# VIEWS PARA CATEGORIAS DE ITEM
# ============================================================================

@login_required
def lista_categorias(request):
    """Lista todas as categorias de itens."""
    search = request.GET.get('search', '')
    categorias = CategoriaItem.objects.annotate(total_itens=Count('itens_por_categoria')).order_by('descricao')
    
    if search:
        categorias = categorias.filter(descricao__icontains=search)
        
    paginator = Paginator(categorias, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Categorias de Itens',
        'singular': 'Categoria',
        'button_text': 'Nova Categoria',
        'create_url': 'itens:criar_categoria',
        'artigo': 'a',
        'empty_message': 'Nenhuma categoria de item cadastrada.',
        'empty_subtitle': 'Comece criando a primeira categoria.'
    }
    return render(request, 'itens/categorias/lista.html', context)

@login_required
def criar_categoria(request):
    """Cria uma nova categoria de item."""
    if request.method == 'POST':
        descricao = request.POST.get('descricao')
        ativo = request.POST.get('ativo') == 'on'
        
        if descricao:
            try:
                CategoriaItem.objects.create(descricao=descricao, ativo=ativo)
                messages.success(request, 'Categoria de item criada com sucesso!')
                return redirect('itens:lista_categorias')
            except Exception as e:
                messages.error(request, f'Erro ao criar categoria: {e}')
        else:
            messages.error(request, 'A descrição é obrigatória.')
            
    context = {
        'title': 'Criar Categoria de Item',
        'back_url': 'itens:lista_categorias'
    }
    return render(request, 'itens/categorias/form.html', context)

@login_required
def editar_categoria(request, pk):
    """Edita uma categoria de item existente."""
    categoria = get_object_or_404(CategoriaItem, pk=pk)
    if request.method == 'POST':
        categoria.descricao = request.POST.get('descricao')
        categoria.ativo = request.POST.get('ativo') == 'on'
        
        if categoria.descricao:
            try:
                categoria.save()
                messages.success(request, 'Categoria de item atualizada com sucesso!')
                return redirect('itens:lista_categorias')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar categoria: {e}')
        else:
            messages.error(request, 'A descrição é obrigatória.')

    context = {
        'object': categoria,
        'title': 'Editar Categoria de Item',
        'back_url': 'itens:lista_categorias'
    }
    return render(request, 'itens/categorias/form.html', context)

@login_required
def deletar_categoria(request, pk):
    """Deleta uma categoria de item."""
    categoria = get_object_or_404(CategoriaItem, pk=pk)
    if request.method == 'POST':
        try:
            categoria.delete()
            messages.success(request, 'Categoria de item deletada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar categoria: {e}')
        return redirect('itens:lista_categorias')
    
    context = {
        'object': categoria,
        'title': 'Categoria de Item'
    }
    return render(request, 'auditorias/deletar_generico.html', context)


# ============================================================================
# VIEWS PARA SUBCATEGORIAS DE ITEM
# ============================================================================

@login_required
def lista_subcategorias(request):
    """Lista todas as subcategorias de itens."""
    search = request.GET.get('search', '')
    subcategorias = SubcategoriaItem.objects.select_related('categoria').annotate(total_itens=Count('itens_por_subcategoria')).order_by('categoria__descricao', 'descricao')
    
    if search:
        subcategorias = subcategorias.filter(
            Q(descricao__icontains=search) | Q(categoria__descricao__icontains=search)
        )
        
    paginator = Paginator(subcategorias, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Subcategorias de Itens',
        'singular': 'Subcategoria',
        'button_text': 'Nova Subcategoria',
        'create_url': 'itens:criar_subcategoria',
        'artigo': 'a',
        'empty_message': 'Nenhuma subcategoria de item cadastrada.',
        'empty_subtitle': 'Comece criando a primeira subcategoria.'
    }
    return render(request, 'itens/subcategorias/lista.html', context)

@login_required
def criar_subcategoria(request):
    """Cria uma nova subcategoria de item."""
    if request.method == 'POST':
        descricao = request.POST.get('descricao')
        categoria_id = request.POST.get('categoria')
        ativo = request.POST.get('ativo') == 'on'
        
        if descricao and categoria_id:
            try:
                categoria = get_object_or_404(CategoriaItem, pk=categoria_id)
                SubcategoriaItem.objects.create(descricao=descricao, categoria=categoria, ativo=ativo)
                messages.success(request, 'Subcategoria de item criada com sucesso!')
                return redirect('itens:lista_subcategorias')
            except Exception as e:
                messages.error(request, f'Erro ao criar subcategoria: {e}')
        else:
            messages.error(request, 'Descrição e Categoria são obrigatórios.')
            
    context = {
        'title': 'Criar Subcategoria de Item',
        'back_url': 'itens:lista_subcategorias',
        'categorias': CategoriaItem.objects.filter(ativo=True)
    }
    return render(request, 'itens/subcategorias/form.html', context)

@login_required
def editar_subcategoria(request, pk):
    """Edita uma subcategoria de item existente."""
    subcategoria = get_object_or_404(SubcategoriaItem, pk=pk)
    if request.method == 'POST':
        subcategoria.descricao = request.POST.get('descricao')
        subcategoria.categoria_id = request.POST.get('categoria')
        subcategoria.ativo = request.POST.get('ativo') == 'on'
        
        if subcategoria.descricao and subcategoria.categoria_id:
            try:
                subcategoria.save()
                messages.success(request, 'Subcategoria de item atualizada com sucesso!')
                return redirect('itens:lista_subcategorias')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar subcategoria: {e}')
        else:
            messages.error(request, 'Descrição e Categoria são obrigatórios.')

    context = {
        'object': subcategoria,
        'title': 'Editar Subcategoria de Item',
        'back_url': 'itens:lista_subcategorias',
        'categorias': CategoriaItem.objects.filter(ativo=True)
    }
    return render(request, 'itens/subcategorias/form.html', context)

@login_required
def deletar_subcategoria(request, pk):
    """Deleta uma subcategoria de item."""
    subcategoria = get_object_or_404(SubcategoriaItem, pk=pk)
    if request.method == 'POST':
        try:
            subcategoria.delete()
            messages.success(request, 'Subcategoria de item deletada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar subcategoria: {e}')
        return redirect('itens:lista_subcategorias')
    
    context = {
        'object': subcategoria,
        'title': 'Subcategoria de Item'
    }
    return render(request, 'auditorias/deletar_generico.html', context)

# ============================================================================
# VIEWS PARA ALMOXARIFADOS
# ============================================================================

@login_required
def lista_almoxarifados(request):
    """Lista todos os almoxarifados."""
    search = request.GET.get('search', '')
    almoxarifados = Almoxarifado.objects.annotate(total_itens=Count('item')).order_by('nome')
    
    if search:
        almoxarifados = almoxarifados.filter(
            Q(nome__icontains=search) | Q(endereco__icontains=search)
        )
        
    paginator = Paginator(almoxarifados, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Almoxarifados',
        'singular': 'Almoxarifado',
        'button_text': 'Novo Almoxarifado',
        'create_url': 'itens:criar_almoxarifado',
        'artigo': 'o',
        'empty_message': 'Nenhum almoxarifado cadastrado.',
        'empty_subtitle': 'Comece criando o primeiro almoxarifado.'
    }
    return render(request, 'itens/almoxarifados/lista.html', context)

@login_required
def criar_almoxarifado(request):
    """Cria um novo almoxarifado."""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        endereco = request.POST.get('endereco')
        ativo = request.POST.get('ativo') == 'on'
        
        if nome:
            try:
                Almoxarifado.objects.create(nome=nome, endereco=endereco, ativo=ativo)
                messages.success(request, 'Almoxarifado criado com sucesso!')
                return redirect('itens:lista_almoxarifados')
            except Exception as e:
                messages.error(request, f'Erro ao criar almoxarifado: {e}')
        else:
            messages.error(request, 'O nome é obrigatório.')
            
    context = {
        'title': 'Criar Almoxarifado',
        'back_url': 'itens:lista_almoxarifados'
    }
    return render(request, 'itens/almoxarifados/form.html', context)

@login_required
def editar_almoxarifado(request, pk):
    """Edita um almoxarifado existente."""
    almoxarifado = get_object_or_404(Almoxarifado, pk=pk)
    if request.method == 'POST':
        almoxarifado.nome = request.POST.get('nome')
        almoxarifado.endereco = request.POST.get('endereco')
        almoxarifado.ativo = request.POST.get('ativo') == 'on'
        
        if almoxarifado.nome:
            try:
                almoxarifado.save()
                messages.success(request, 'Almoxarifado atualizado com sucesso!')
                return redirect('itens:lista_almoxarifados')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar almoxarifado: {e}')
        else:
            messages.error(request, 'O nome é obrigatório.')

    context = {
        'object': almoxarifado,
        'title': 'Editar Almoxarifado',
        'back_url': 'itens:lista_almoxarifados'
    }
    return render(request, 'itens/almoxarifados/form.html', context)

@login_required
def deletar_almoxarifado(request, pk):
    """Deleta um almoxarifado."""
    almoxarifado = get_object_or_404(Almoxarifado, pk=pk)
    if request.method == 'POST':
        try:
            almoxarifado.delete()
            messages.success(request, 'Almoxarifado deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar almoxarifado: {e}')
        return redirect('itens:lista_almoxarifados')
    
    context = {
        'object': almoxarifado,
        'title': 'Almoxarifado'
    }
    return render(request, 'auditorias/deletar_generico.html', context)

# ============================================================================
# VIEWS PARA ITENS
# ============================================================================

@login_required
def lista_itens(request):
    """Lista todos os itens com busca e paginação."""
    search = request.GET.get('search', '')
    itens_list = Item.objects.select_related(
        'unidade_medida', 
        'categoria_principal', 
        'subcategoria_principal', 
        'almoxarifado'
    ).order_by('codigo_interno')

    if search:
        itens_list = itens_list.filter(
            Q(codigo_interno__icontains=search) |
            Q(descricao__icontains=search) |
            Q(categoria_principal__descricao__icontains=search) |
            Q(almoxarifado__nome__icontains=search)
        )

    paginator = Paginator(itens_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Itens',
        'singular': 'Item',
        'button_text': 'Novo Item',
        'create_url': 'itens:criar_item',
        'artigo': 'o',
        'empty_message': 'Nenhum item cadastrado',
        'empty_subtitle': 'Comece criando o primeiro item.'
    }
    return render(request, 'itens/lista.html', context)

@login_required
def criar_item(request):
    """Cria um novo item."""
    if request.method == 'POST':
        # Tratamento de dados do form
        codigo_interno = request.POST.get('codigo_interno')
        descricao = request.POST.get('descricao')

        if not codigo_interno or not descricao:
            messages.error(request, 'Código Interno e Descrição são obrigatórios.')
        else:
            try:
                item = Item(
                    codigo_interno=codigo_interno,
                    descricao=descricao,
                    codigo_alternativo=request.POST.get('codigo_alternativo'),
                    peso=request.POST.get('peso') or None,
                    valor=request.POST.get('valor') or None,
                    ativo=request.POST.get('ativo') == 'on',
                    unidade_medida_id=request.POST.get('unidade_medida') or None,
                    almoxarifado_id=request.POST.get('almoxarifado') or None,
                    categoria_principal_id=request.POST.get('categoria_principal') or None,
                    subcategoria_principal_id=request.POST.get('subcategoria_principal') or None,
                )
                if request.FILES.get('imagem_item'):
                    item.imagem_item = request.FILES['imagem_item']

                item.save()
                messages.success(request, f"Item '{item.descricao}' criado com sucesso!")
                return redirect('itens:lista_itens')
            except Exception as e:
                messages.error(request, f"Erro ao criar o item: {e}")

    context = {
        'title': 'Criar Item',
        'back_url': 'itens:lista_itens',
        'unidades_medida': UnidadeMedida.objects.filter(ativo=True),
        'almoxarifados': Almoxarifado.objects.filter(ativo=True),
        'categorias': CategoriaItem.objects.filter(ativo=True),
        'subcategorias': SubcategoriaItem.objects.filter(ativo=True),
    }
    return render(request, 'itens/form.html', context)

@login_required
def editar_item(request, pk):
    """Edita um item existente."""
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        codigo_interno = request.POST.get('codigo_interno')
        descricao = request.POST.get('descricao')

        if not codigo_interno or not descricao:
            messages.error(request, 'Código Interno e Descrição são obrigatórios.')
        else:
            try:
                item.codigo_interno = codigo_interno
                item.descricao = descricao
                item.codigo_alternativo = request.POST.get('codigo_alternativo')
                item.peso = request.POST.get('peso') or None
                item.valor = request.POST.get('valor') or None
                item.ativo = request.POST.get('ativo') == 'on'
                item.unidade_medida_id = request.POST.get('unidade_medida') or None
                item.almoxarifado_id = request.POST.get('almoxarifado') or None
                item.categoria_principal_id = request.POST.get('categoria_principal') or None
                item.subcategoria_principal_id = request.POST.get('subcategoria_principal') or None
                
                if request.FILES.get('imagem_item'):
                    item.imagem_item = request.FILES['imagem_item']

                item.save()
                messages.success(request, f"Item '{item.descricao}' atualizado com sucesso!")
                return redirect('itens:lista_itens')
            except Exception as e:
                messages.error(request, f"Erro ao atualizar o item: {e}")

    context = {
        'object': item,
        'title': 'Editar Item',
        'back_url': 'itens:lista_itens',
        'unidades_medida': UnidadeMedida.objects.filter(ativo=True),
        'almoxarifados': Almoxarifado.objects.filter(ativo=True),
        'categorias': CategoriaItem.objects.filter(ativo=True),
        'subcategorias': SubcategoriaItem.objects.filter(ativo=True),
    }
    return render(request, 'itens/form.html', context)


@login_required
def deletar_item(request, pk):
    """Deleta um item."""
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        try:
            item_desc = item.descricao
            item.delete()
            messages.success(request, f"Item '{item_desc}' deletado com sucesso!")
        except Exception as e:
            messages.error(request, f"Erro ao deletar o item: {e}")
        return redirect('itens:lista_itens')

    context = {
        'object': item,
        'title': 'Item'
    }
    return render(request, 'auditorias/deletar_generico.html', context)

# AJAX view to get subcategories for a category
@login_required
def get_subcategorias_por_categoria(request):
    """Retorna subcategorias de uma categoria via AJAX"""
    categoria_id = request.GET.get('categoria_id')
    subcategorias = SubcategoriaItem.objects.filter(categoria_id=categoria_id, ativo=True).values('id', 'descricao')
    return JsonResponse(list(subcategorias), safe=False)