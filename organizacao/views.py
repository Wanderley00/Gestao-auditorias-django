# organizacao/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Empresa, Area, Setor, SubSetor
from usuarios.models import Usuario

# ============================================================================
# VIEWS PARA EMPRESAS
# ============================================================================

@login_required
def lista_empresas(request):
    """Lista todas as empresas."""
    search = request.GET.get('search', '')
    empresas = Empresa.objects.all()
    if search:
        empresas = empresas.filter(Q(nome__icontains=search) | Q(cnpj__icontains=search))
    
    paginator = Paginator(empresas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Empresas',
        'singular': 'Empresa',
        'button_text': 'Nova Empresa',
        'create_url': 'organizacao:criar_empresa',
        'artigo': 'a',
        'empty_message': 'Nenhuma empresa cadastrada.',
        'empty_subtitle': 'Comece criando a primeira empresa.'
    }
    return render(request, 'organizacao/empresas/lista.html', context)

@login_required
def criar_empresa(request):
    """Cria uma nova empresa."""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if nome:
            try:
                Empresa.objects.create(
                    nome=nome,
                    cnpj=request.POST.get('cnpj'),
                    endereco=request.POST.get('endereco'),
                    ativo=request.POST.get('ativo') == 'on',
                    usuario_responsavel_id=request.POST.get('usuario_responsavel') or None
                )
                messages.success(request, 'Empresa criada com sucesso!')
                return redirect('organizacao:lista_empresas')
            except Exception as e:
                messages.error(request, f'Erro ao criar empresa: {e}')
        else:
            messages.error(request, 'O nome da empresa é obrigatório.')
    
    context = {
        'title': 'Criar Empresa',
        'back_url': 'organizacao:lista_empresas',
        'usuarios': Usuario.objects.filter(is_active=True)
    }
    return render(request, 'organizacao/empresas/form.html', context)

@login_required
def editar_empresa(request, pk):
    """Edita uma empresa existente."""
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if nome:
            try:
                empresa.nome = nome
                empresa.cnpj = request.POST.get('cnpj')
                empresa.endereco = request.POST.get('endereco')
                empresa.ativo = request.POST.get('ativo') == 'on'
                empresa.usuario_responsavel_id = request.POST.get('usuario_responsavel') or None
                empresa.save()
                messages.success(request, 'Empresa atualizada com sucesso!')
                return redirect('organizacao:lista_empresas')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar empresa: {e}')
        else:
            messages.error(request, 'O nome da empresa é obrigatório.')
            
    context = {
        'object': empresa,
        'title': 'Editar Empresa',
        'back_url': 'organizacao:lista_empresas',
        'usuarios': Usuario.objects.filter(is_active=True)
    }
    return render(request, 'organizacao/empresas/form.html', context)

@login_required
def deletar_empresa(request, pk):
    """Deleta uma empresa."""
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        try:
            empresa.delete()
            messages.success(request, 'Empresa deletada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar empresa: {e}')
        return redirect('organizacao:lista_empresas')
    
    context = {'object': empresa, 'title': 'Empresa'}
    return render(request, 'auditorias/deletar_generico.html', context)

# ============================================================================
# VIEWS PARA ÁREAS
# ============================================================================

@login_required
def lista_areas(request):
    """Lista todas as áreas."""
    search = request.GET.get('search', '')
    areas = Area.objects.select_related('empresa').all()
    if search:
        areas = areas.filter(Q(nome__icontains=search) | Q(empresa__nome__icontains=search))
    
    paginator = Paginator(areas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Áreas',
        'singular': 'Área',
        'button_text': 'Nova Área',
        'create_url': 'organizacao:criar_area',
        'artigo': 'a',
        'empty_message': 'Nenhuma área cadastrada.',
        'empty_subtitle': 'Comece criando a primeira área.'
    }
    return render(request, 'organizacao/areas/lista.html', context)

@login_required
def criar_area(request):
    """Cria uma nova área."""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        empresa_id = request.POST.get('empresa')
        if nome and empresa_id:
            try:
                Area.objects.create(
                    nome=nome,
                    empresa_id=empresa_id,
                    ativo=request.POST.get('ativo') == 'on',
                    usuario_responsavel_id=request.POST.get('usuario_responsavel') or None
                )
                messages.success(request, 'Área criada com sucesso!')
                return redirect('organizacao:lista_areas')
            except Exception as e:
                messages.error(request, f'Erro ao criar área: {e}')
        else:
            messages.error(request, 'Nome e Empresa são obrigatórios.')
    
    context = {
        'title': 'Criar Área',
        'back_url': 'organizacao:lista_areas',
        'empresas': Empresa.objects.filter(ativo=True),
        'usuarios': Usuario.objects.filter(is_active=True)
    }
    return render(request, 'organizacao/areas/form.html', context)

@login_required
def editar_area(request, pk):
    """Edita uma área existente."""
    area = get_object_or_404(Area, pk=pk)
    if request.method == 'POST':
        nome = request.POST.get('nome')
        empresa_id = request.POST.get('empresa')
        if nome and empresa_id:
            try:
                area.nome = nome
                area.empresa_id = empresa_id
                area.ativo = request.POST.get('ativo') == 'on'
                area.usuario_responsavel_id = request.POST.get('usuario_responsavel') or None
                area.save()
                messages.success(request, 'Área atualizada com sucesso!')
                return redirect('organizacao:lista_areas')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar área: {e}')
        else:
            messages.error(request, 'Nome e Empresa são obrigatórios.')
            
    context = {
        'object': area,
        'title': 'Editar Área',
        'back_url': 'organizacao:lista_areas',
        'empresas': Empresa.objects.filter(ativo=True),
        'usuarios': Usuario.objects.filter(is_active=True)
    }
    return render(request, 'organizacao/areas/form.html', context)

@login_required
def deletar_area(request, pk):
    """Deleta uma área."""
    area = get_object_or_404(Area, pk=pk)
    if request.method == 'POST':
        try:
            area.delete()
            messages.success(request, 'Área deletada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar área: {e}')
        return redirect('organizacao:lista_areas')
    
    context = {'object': area, 'title': 'Área'}
    return render(request, 'auditorias/deletar_generico.html', context)

# ============================================================================
# VIEWS PARA SETORES
# ============================================================================

@login_required
def lista_setores(request):
    """Lista todos os setores."""
    search = request.GET.get('search', '')
    setores = Setor.objects.select_related('area__empresa').all()
    if search:
        setores = setores.filter(Q(nome__icontains=search) | Q(area__nome__icontains=search) | Q(area__empresa__nome__icontains=search))
    
    paginator = Paginator(setores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Setores',
        'singular': 'Setor',
        'button_text': 'Novo Setor',
        'create_url': 'organizacao:criar_setor',
        'artigo': 'o',
        'empty_message': 'Nenhum setor cadastrado.',
        'empty_subtitle': 'Comece criando o primeiro setor.'
    }
    return render(request, 'organizacao/setores/lista.html', context)

@login_required
def criar_setor(request):
    """Cria um novo setor."""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        area_id = request.POST.get('area')
        if nome and area_id:
            try:
                Setor.objects.create(
                    nome=nome,
                    area_id=area_id,
                    ativo=request.POST.get('ativo') == 'on',
                    usuario_responsavel_id=request.POST.get('usuario_responsavel') or None
                )
                messages.success(request, 'Setor criado com sucesso!')
                return redirect('organizacao:lista_setores')
            except Exception as e:
                messages.error(request, f'Erro ao criar setor: {e}')
        else:
            messages.error(request, 'Nome e Área são obrigatórios.')
    
    context = {
        'title': 'Criar Setor',
        'back_url': 'organizacao:lista_setores',
        'areas': Area.objects.filter(ativo=True),
        'usuarios': Usuario.objects.filter(is_active=True)
    }
    return render(request, 'organizacao/setores/form.html', context)

@login_required
def editar_setor(request, pk):
    """Edita um setor existente."""
    setor = get_object_or_404(Setor, pk=pk)
    if request.method == 'POST':
        nome = request.POST.get('nome')
        area_id = request.POST.get('area')
        if nome and area_id:
            try:
                setor.nome = nome
                setor.area_id = area_id
                setor.ativo = request.POST.get('ativo') == 'on'
                setor.usuario_responsavel_id = request.POST.get('usuario_responsavel') or None
                setor.save()
                messages.success(request, 'Setor atualizado com sucesso!')
                return redirect('organizacao:lista_setores')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar setor: {e}')
        else:
            messages.error(request, 'Nome e Área são obrigatórios.')
            
    context = {
        'object': setor,
        'title': 'Editar Setor',
        'back_url': 'organizacao:lista_setores',
        'areas': Area.objects.filter(ativo=True),
        'usuarios': Usuario.objects.filter(is_active=True)
    }
    return render(request, 'organizacao/setores/form.html', context)

@login_required
def deletar_setor(request, pk):
    """Deleta um setor."""
    setor = get_object_or_404(Setor, pk=pk)
    if request.method == 'POST':
        try:
            setor.delete()
            messages.success(request, 'Setor deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar setor: {e}')
        return redirect('organizacao:lista_setores')
    
    context = {'object': setor, 'title': 'Setor'}
    return render(request, 'auditorias/deletar_generico.html', context)

# ============================================================================
# VIEWS PARA SUBSETORES
# ============================================================================

@login_required
def lista_subsetores(request):
    """Lista todos os subsetores."""
    search = request.GET.get('search', '')
    subsetores = SubSetor.objects.select_related('setor__area__empresa').all()
    if search:
        subsetores = subsetores.filter(Q(nome__icontains=search) | Q(setor__nome__icontains=search) | Q(setor__area__nome__icontains=search))
    
    paginator = Paginator(subsetores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Subsetores',
        'singular': 'Subsetor',
        'button_text': 'Novo Subsetor',
        'create_url': 'organizacao:criar_subsetor',
        'artigo': 'o',
        'empty_message': 'Nenhum subsetor cadastrado.',
        'empty_subtitle': 'Comece criando o primeiro subsetor.'
    }
    return render(request, 'organizacao/subsetores/lista.html', context)

@login_required
def criar_subsetor(request):
    """Cria um novo subsetor."""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        setor_id = request.POST.get('setor')
        if nome and setor_id:
            try:
                SubSetor.objects.create(
                    nome=nome,
                    setor_id=setor_id,
                    ativo=request.POST.get('ativo') == 'on',
                    usuario_responsavel_id=request.POST.get('usuario_responsavel') or None
                )
                messages.success(request, 'Subsetor criado com sucesso!')
                return redirect('organizacao:lista_subsetores')
            except Exception as e:
                messages.error(request, f'Erro ao criar subsetor: {e}')
        else:
            messages.error(request, 'Nome e Setor são obrigatórios.')
    
    context = {
        'title': 'Criar Subsetor',
        'back_url': 'organizacao:lista_subsetores',
        'setores': Setor.objects.filter(ativo=True),
        'usuarios': Usuario.objects.filter(is_active=True)
    }
    return render(request, 'organizacao/subsetores/form.html', context)

@login_required
def editar_subsetor(request, pk):
    """Edita um subsetor existente."""
    subsetor = get_object_or_404(SubSetor, pk=pk)
    if request.method == 'POST':
        nome = request.POST.get('nome')
        setor_id = request.POST.get('setor')
        if nome and setor_id:
            try:
                subsetor.nome = nome
                subsetor.setor_id = setor_id
                subsetor.ativo = request.POST.get('ativo') == 'on'
                subsetor.usuario_responsavel_id = request.POST.get('usuario_responsavel') or None
                subsetor.save()
                messages.success(request, 'Subsetor atualizado com sucesso!')
                return redirect('organizacao:lista_subsetores')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar subsetor: {e}')
        else:
            messages.error(request, 'Nome e Setor são obrigatórios.')
            
    context = {
        'object': subsetor,
        'title': 'Editar Subsetor',
        'back_url': 'organizacao:lista_subsetores',
        'setores': Setor.objects.filter(ativo=True),
        'usuarios': Usuario.objects.filter(is_active=True)
    }
    return render(request, 'organizacao/subsetores/form.html', context)

@login_required
def deletar_subsetor(request, pk):
    """Deleta um subsetor."""
    subsetor = get_object_or_404(SubSetor, pk=pk)
    if request.method == 'POST':
        try:
            subsetor.delete()
            messages.success(request, 'Subsetor deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar subsetor: {e}')
        return redirect('organizacao:lista_subsetores')
    
    context = {'object': subsetor, 'title': 'Subsetor'}
    return render(request, 'auditorias/deletar_generico.html', context)