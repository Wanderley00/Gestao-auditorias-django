# fornecedores/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Fornecedor
from usuarios.models import Usuario

@login_required
def lista_fornecedores(request):
    """Lista todos os fornecedores com busca e paginação."""
    search = request.GET.get('search', '')
    fornecedores = Fornecedor.objects.select_related('usuario_responsavel').order_by('nome')

    if search:
        fornecedores = fornecedores.filter(
            Q(nome__icontains=search) |
            Q(npr__icontains=search) |
            Q(usuario_responsavel__username__icontains=search)
        )

    paginator = Paginator(fornecedores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Fornecedores',
        'singular': 'Fornecedor',
        'button_text': 'Novo Fornecedor',
        'create_url': 'fornecedores:criar_fornecedor',
        'artigo': 'o',
        'empty_message': 'Nenhum fornecedor cadastrado.',
        'empty_subtitle': 'Comece criando o primeiro fornecedor.'
    }
    return render(request, 'fornecedores/lista.html', context)

@login_required
def criar_fornecedor(request):
    """Cria um novo fornecedor."""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if not nome:
            messages.error(request, 'O nome do fornecedor é obrigatório.')
        else:
            try:
                Fornecedor.objects.create(
                    nome=nome,
                    npr=request.POST.get('npr'),
                    ativo=request.POST.get('ativo') == 'on',
                    usuario_responsavel_id=request.POST.get('usuario_responsavel') or None
                )
                messages.success(request, 'Fornecedor criado com sucesso!')
                return redirect('fornecedores:lista_fornecedores')
            except Exception as e:
                messages.error(request, f'Erro ao criar fornecedor: {e}')

    context = {
        'title': 'Criar Fornecedor',
        'back_url': 'fornecedores:lista_fornecedores',
        'usuarios': Usuario.objects.filter(is_active=True)
    }
    return render(request, 'fornecedores/form.html', context)

@login_required
def editar_fornecedor(request, pk):
    """Edita um fornecedor existente."""
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if not nome:
            messages.error(request, 'O nome do fornecedor é obrigatório.')
        else:
            try:
                fornecedor.nome = nome
                fornecedor.npr = request.POST.get('npr')
                fornecedor.ativo = request.POST.get('ativo') == 'on'
                fornecedor.usuario_responsavel_id = request.POST.get('usuario_responsavel') or None
                fornecedor.save()
                messages.success(request, 'Fornecedor atualizado com sucesso!')
                return redirect('fornecedores:lista_fornecedores')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar fornecedor: {e}')

    context = {
        'object': fornecedor,
        'title': 'Editar Fornecedor',
        'back_url': 'fornecedores:lista_fornecedores',
        'usuarios': Usuario.objects.filter(is_active=True)
    }
    return render(request, 'fornecedores/form.html', context)

@login_required
def deletar_fornecedor(request, pk):
    """Deleta um fornecedor."""
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    if request.method == 'POST':
        try:
            fornecedor.delete()
            messages.success(request, 'Fornecedor deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar fornecedor: {e}')
        return redirect('fornecedores:lista_fornecedores')

    context = {
        'object': fornecedor,
        'title': 'Fornecedor'
    }
    return render(request, 'auditorias/deletar_generico.html', context)
