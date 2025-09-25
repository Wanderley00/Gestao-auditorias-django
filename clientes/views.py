# clientes/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Cliente
from usuarios.models import Usuario

@login_required
def lista_clientes(request):
    """Lista todos os clientes com busca e paginação."""
    search = request.GET.get('search', '')
    clientes = Cliente.objects.select_related('usuario_responsavel').order_by('nome')

    if search:
        clientes = clientes.filter(
            Q(nome__icontains=search) |
            Q(npr__icontains=search) |
            Q(email__icontains=search) |
            Q(usuario_responsavel__username__icontains=search)
        )

    paginator = Paginator(clientes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Clientes',
        'singular': 'Cliente',
        'button_text': 'Novo Cliente',
        'create_url': 'clientes:criar_cliente',
        'artigo': 'o',
        'empty_message': 'Nenhum cliente cadastrado.',
        'empty_subtitle': 'Comece criando o primeiro cliente.'
    }
    return render(request, 'clientes/lista.html', context)

@login_required
def criar_cliente(request):
    """Cria um novo cliente."""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if not nome:
            messages.error(request, 'O nome do cliente é obrigatório.')
        else:
            try:
                cliente = Cliente(
                    nome=nome,
                    npr=request.POST.get('npr'),
                    email=request.POST.get('email'),
                    ativo=request.POST.get('ativo') == 'on',
                    usuario_responsavel_id=request.POST.get('usuario_responsavel') or None
                )
                if request.FILES.get('logo_cliente'):
                    cliente.logo_cliente = request.FILES['logo_cliente']
                
                cliente.save()
                messages.success(request, 'Cliente criado com sucesso!')
                return redirect('clientes:lista_clientes')
            except Exception as e:
                messages.error(request, f'Erro ao criar cliente: {e}')

    context = {
        'title': 'Criar Cliente',
        'back_url': 'clientes:lista_clientes',
        'usuarios': Usuario.objects.filter(is_active=True)
    }
    return render(request, 'clientes/form.html', context)

@login_required
def editar_cliente(request, pk):
    """Edita um cliente existente."""
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if not nome:
            messages.error(request, 'O nome do cliente é obrigatório.')
        else:
            try:
                cliente.nome = nome
                cliente.npr = request.POST.get('npr')
                cliente.email = request.POST.get('email')
                cliente.ativo = request.POST.get('ativo') == 'on'
                cliente.usuario_responsavel_id = request.POST.get('usuario_responsavel') or None
                
                if request.FILES.get('logo_cliente'):
                    cliente.logo_cliente = request.FILES['logo_cliente']

                cliente.save()
                messages.success(request, 'Cliente atualizado com sucesso!')
                return redirect('clientes:lista_clientes')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar cliente: {e}')

    context = {
        'object': cliente,
        'title': 'Editar Cliente',
        'back_url': 'clientes:lista_clientes',
        'usuarios': Usuario.objects.filter(is_active=True)
    }
    return render(request, 'clientes/form.html', context)

@login_required
def deletar_cliente(request, pk):
    """Deleta um cliente."""
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        try:
            cliente.delete()
            messages.success(request, 'Cliente deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar cliente: {e}')
        return redirect('clientes:lista_clientes')

    context = {
        'object': cliente,
        'title': 'Cliente'
    }
    return render(request, 'auditorias/deletar_generico.html', context)
