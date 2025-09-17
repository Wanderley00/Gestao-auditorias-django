# itens/views.py (corrigido)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Item, CategoriaItem, SubcategoriaItem, Almoxarifado
from cadastros_base.models import UnidadeMedida

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

    paginator = Paginator(itens_list, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': 'Itens',
        'singular': 'Item',
        'button_text': 'Novo Item',
        'page_obj': page_obj,
        'search': search,
        'create_url': 'itens:criar_item',
        'artigo': 'o',
        'empty_message': 'Nenhum item cadastrado',
        'empty_subtitle': 'Comece criando o primeiro item.'
    }
    return render(request, 'itens/lista_itens.html', context)

@login_required
def criar_item(request):
    """Cria um novo item."""
    if request.method == 'POST':
        try:
            item = Item(
                codigo_interno=request.POST.get('codigo_interno'),
                descricao=request.POST.get('descricao'),
                codigo_alternativo=request.POST.get('codigo_alternativo'),
                peso=request.POST.get('peso') or None,
                valor=request.POST.get('valor') or None,
                ativo=request.POST.get('ativo') == 'on',
                unidade_medida_id=request.POST.get('unidade_medida') or None,
                almoxarifado_id=request.POST.get('almoxarifado') or None,
                categoria_principal_id=request.POST.get('categoria_principal') or None,
                subcategoria_principal_id=request.POST.get('subcategoria_principal') or None,
            )
            item.save()
            messages.success(request, f"Item '{item.descricao}' criado com sucesso!")
            return redirect('itens:lista_itens')
        except Exception as e:
            messages.error(request, f"Erro ao criar o item: {e}")

    context = {
        'title': 'Adicionar Item',
        'subtitle': 'Preencha os dados para cadastrar um novo item',
        'back_url': 'itens:lista_itens',
        'unidades_medida': UnidadeMedida.objects.filter(ativo=True),
        'almoxarifados': Almoxarifado.objects.filter(ativo=True),
        'categorias': CategoriaItem.objects.filter(ativo=True),
        'subcategorias': SubcategoriaItem.objects.filter(ativo=True),
    }
    return render(request, 'itens/form_item.html', context)

@login_required
def editar_item(request, pk):
    """Edita um item existente."""
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        try:
            item.codigo_interno = request.POST.get('codigo_interno')
            item.descricao = request.POST.get('descricao')
            item.codigo_alternativo = request.POST.get('codigo_alternativo')
            item.peso = request.POST.get('peso') or None
            item.valor = request.POST.get('valor') or None
            item.ativo = request.POST.get('ativo') == 'on'
            item.unidade_medida_id = request.POST.get('unidade_medida') or None
            item.almoxarifado_id = request.POST.get('almoxarifado') or None
            item.categoria_principal_id = request.POST.get('categoria_principal') or None
            item.subcategoria_principal_id = request.POST.get('subcategoria_principal') or None
            
            item.save()
            messages.success(request, f"Item '{item.descricao}' atualizado com sucesso!")
            return redirect('itens:lista_itens')
        except Exception as e:
            messages.error(request, f"Erro ao atualizar o item: {e}")

    context = {
        'title': 'Editar Item',
        'subtitle': f"Você está editando o item '{item.codigo_interno}'",
        'back_url': 'itens:lista_itens',
        'item': item,
        'unidades_medida': UnidadeMedida.objects.filter(ativo=True),
        'almoxarifados': Almoxarifado.objects.filter(ativo=True),
        'categorias': CategoriaItem.objects.filter(ativo=True),
        'subcategorias': SubcategoriaItem.objects.filter(ativo=True),
    }
    return render(request, 'itens/form_item.html', context)

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
        'title': 'Confirmar Exclusão',
        'item': item,
    }
    return render(request, 'itens/deletar_item.html', context)