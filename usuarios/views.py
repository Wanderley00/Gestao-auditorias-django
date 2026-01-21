# usuarios/views.py

from django.contrib.auth.models import Permission
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import Group, Permission
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.contenttypes.models import ContentType
import csv
from django.http import HttpResponse
import json

from django.contrib.auth.decorators import login_required, permission_required

from .models import Usuario, DetalheGrupo

from collections import defaultdict

from .serializers import UsuarioSerializer

from .models import Usuario

from .serializers import AlterarSenhaSerializer

from django.db.models import Count

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.generics import RetrieveUpdateAPIView, UpdateAPIView

# Decorator para verificar se o usuário é administrador


def admin_required(user):
    return user.is_superuser or user.is_staff


# ============================================================================
# VIEWS PARA USUÁRIOS
# ============================================================================

@login_required
@permission_required('usuarios.view_usuario', raise_exception=True)
def dashboard_usuarios(request):
    """Dashboard principal do módulo de usuários."""
    context = {
        'total_usuarios': Usuario.objects.count(),
        'usuarios_ativos': Usuario.objects.filter(is_active=True).count(),
        'usuarios_staff': Usuario.objects.filter(is_staff=True).count(),
        'total_grupos': Group.objects.count(),
        'usuarios_recentes': Usuario.objects.order_by('-date_joined')[:5],
        'title': 'Dashboard de Usuários'
    }
    return render(request, 'usuarios/dashboard.html', context)


@login_required
# <--- TRAVA FORTE: SÓ SUPERUSUÁRIO
@user_passes_test(lambda u: u.is_superuser)
def alterar_senha_usuario(request, pk):
    """Altera a senha de um usuário específico (Apenas Superusuário)"""
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if not password:
            messages.error(request, 'A senha é obrigatória!')
        elif password != password_confirm:
            messages.error(request, 'As senhas não coincidem!')
        elif len(password) < 8:
            messages.error(
                request, 'A senha deve ter pelo menos 8 caracteres!')
        else:
            try:
                usuario.set_password(password)
                usuario.save()
                messages.success(request, 'Senha alterada com sucesso!')
                return redirect('usuarios:lista_usuarios')
            except Exception as e:
                messages.error(request, f'Erro ao alterar senha: {str(e)}')

    context = {
        'usuario': usuario,
        'title': f'Alterar Senha - {usuario.get_full_name() or usuario.username}'
    }
    return render(request, 'usuarios/alterar_senha.html', context)


@login_required
@permission_required('usuarios.view_usuario', raise_exception=True)
def lista_usuarios(request):
    """Lista todos os usuários com busca e paginação"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    grupo = request.GET.get('grupo', '')

    usuarios = Usuario.objects.all()

    if search:
        usuarios = usuarios.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    if status == 'ativo':
        usuarios = usuarios.filter(is_active=True)
    elif status == 'inativo':
        usuarios = usuarios.filter(is_active=False)
    elif status == 'staff':
        usuarios = usuarios.filter(is_staff=True)

    if grupo:
        usuarios = usuarios.filter(groups__id=grupo)

    usuarios = usuarios.order_by('-date_joined')

    paginator = Paginator(usuarios, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'grupo': grupo,
        'grupos': Group.objects.all(),
        'title': 'Usuários',
        'singular': 'Usuário',
        'button_text': 'Novo Usuário',
        'create_url': 'usuarios:criar_usuario',
        'artigo': 'o',
    }
    return render(request, 'usuarios/lista.html', context)


@login_required
@permission_required('usuarios.add_usuario', raise_exception=True)
def criar_usuario(request):
    """Cria um novo usuário"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        is_active = request.POST.get('is_active') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        # MUDANÇA 1: Pegamos apenas 'grupo' (singular)
        grupo_id = request.POST.get('grupo')

        # Validações
        if not username or not email or not password:
            messages.error(
                request, 'Username, email e senha são obrigatórios!')
        elif not grupo_id:  # <--- NOVA VALIDAÇÃO AQUI
            messages.error(
                request, 'É obrigatório selecionar um Perfil de Acesso (Grupo)!')
        elif password != password_confirm:
            messages.error(request, 'As senhas não coincidem!')
        elif Usuario.objects.filter(username=username).exists():
            messages.error(request, 'Este username já está em uso!')
        elif Usuario.objects.filter(email=email).exists():
            messages.error(request, 'Este email já está em uso!')
        else:
            try:
                # Criação do usuário (código igual ao seu)
                usuario = Usuario.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=request.POST.get('is_active') == 'on',
                    is_staff=request.POST.get('is_staff') == 'on',
                    is_superuser=request.POST.get('is_superuser') == 'on'
                )

                # MUDANÇA 2: Lógica de atribuição de grupo único
                if grupo_id:
                    grupo = Group.objects.get(id=grupo_id)
                    usuario.groups.add(grupo)

                messages.success(request, 'Usuário criado com sucesso!')
                return redirect('usuarios:lista_usuarios')
            except Exception as e:
                messages.error(request, f'Erro ao criar usuário: {str(e)}')

    # GET: Mandamos os grupos para preencher o <select>
    context = {
        'grupos': Group.objects.all().order_by('name'),
        'title': 'Criar Usuário'
    }
    # Ajuste o nome do template se necessário
    return render(request, 'usuarios/form_usuario.html', context)


@login_required
@permission_required('usuarios.change_usuario', raise_exception=True)
def editar_usuario(request, pk):
    """Edita um usuário existente"""
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        usuario.username = request.POST.get('username')
        usuario.email = request.POST.get('email')
        usuario.first_name = request.POST.get('first_name')
        usuario.last_name = request.POST.get('last_name')
        usuario.is_active = request.POST.get('is_active') == 'on'
        usuario.is_staff = request.POST.get('is_staff') == 'on'
        usuario.is_superuser = request.POST.get('is_superuser') == 'on'
        grupo_id = request.POST.get('grupo')  # MUDANÇA 1

        if not grupo_id:  # <--- NOVA VALIDAÇÃO AQUI
            messages.error(
                request, 'É obrigatório selecionar um Perfil de Acesso (Grupo)!')
        # Validar username único (exceto o próprio usuário)
        elif Usuario.objects.filter(username=usuario.username).exclude(pk=pk).exists():
            messages.error(request, 'Este username já está em uso!')
        # Validar email único (exceto o próprio usuário)
        elif Usuario.objects.filter(email=usuario.email).exclude(pk=pk).exists():
            messages.error(request, 'Este email já está em uso!')
        else:
            try:
                usuario.username = request.POST.get('username')
                usuario.save()

                # MUDANÇA 2: Atualizar o grupo
                if grupo_id:
                    novo_grupo = Group.objects.get(id=grupo_id)
                    usuario.groups.clear()
                    usuario.groups.add(novo_grupo)
                else:
                    usuario.groups.clear()  # Se não selecionou nada, remove permissões

                messages.success(request, 'Usuário atualizado com sucesso!')
                return redirect('usuarios:lista_usuarios')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar usuário: {str(e)}')

    # MUDANÇA 3: Descobrir qual o grupo atual para marcar no HTML
    grupo_atual = usuario.groups.first()  # Pega o primeiro grupo encontrado

    context = {
        'usuario': usuario,
        'grupos': Group.objects.all().order_by('name'),
        # Envia o ID para o template
        'grupo_atual_id': grupo_atual.id if grupo_atual else None,
        'title': 'Editar Usuário'
    }
    return render(request, 'usuarios/form_usuario.html', context)


@login_required
@user_passes_test(admin_required)
def deletar_usuario(request, pk):
    """Deleta um usuário"""
    usuario = get_object_or_404(Usuario, pk=pk)

    # Não permitir deletar o próprio usuário
    if usuario == request.user:
        messages.error(request, 'Você não pode deletar sua própria conta!')
        return redirect('usuarios:lista_usuarios')

    if request.method == 'POST':
        try:
            usuario.delete()
            messages.success(request, 'Usuário deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar usuário: {str(e)}')
        return redirect('usuarios:lista_usuarios')

    context = {
        'usuario': usuario,
        'title': 'Deletar Usuário'
    }
    return render(request, 'usuarios/deletar.html', context)


# ============================================================================
# VIEWS PARA GRUPOS E PERMISSÕES
# ============================================================================
# Função auxiliar para organizar as permissões (Evita repetir código)
# Em usuarios/views.py

def get_permissions_dict():
    """
    Organiza as permissões em uma estrutura de matriz:
    Módulo -> Model -> {add, change, delete, view}
    """
    ignorar_models = ['session', 'content type',
                      'log entry', 'permission', 'group']

    # Busca todas as permissões relevantes
    perms = Permission.objects.exclude(content_type__model__in=ignorar_models)\
        .select_related('content_type')\
        .order_by('content_type__app_label', 'content_type__model')

    estrutura = {}

    for p in perms:
        # Nome do App (Ex: Auditorias, Usuários)
        app_label = p.content_type.app_label
        # Nome do Model (Ex: Auditoria, Agendamento)
        model_name = p.content_type.model
        # Nome Bonito para exibir (Ex: "Agendamento de Auditoria")
        nome_exibicao = p.content_type.name.title()

        # Cria a chave do App se não existir
        # Mapeamento para nomes mais bonitos se quiser
        app_nome = app_label.title()
        if app_label == 'auth':
            app_nome = 'Administração'
        if app_label == 'usuarios':
            app_nome = 'Gestão de Acesso'

        if app_nome not in estrutura:
            estrutura[app_nome] = {}

        # Cria a chave do Model dentro do App
        if model_name not in estrutura[app_nome]:
            estrutura[app_nome][model_name] = {
                'nome': nome_exibicao,
                'acoes': {}
            }

        # Identifica a ação baseada no codename (add_user, change_user...)
        codename = p.codename
        if codename.startswith('add_'):
            estrutura[app_nome][model_name]['acoes']['add'] = p
        elif codename.startswith('change_'):
            estrutura[app_nome][model_name]['acoes']['change'] = p
        elif codename.startswith('delete_'):
            estrutura[app_nome][model_name]['acoes']['delete'] = p
        elif codename.startswith('view_'):
            estrutura[app_nome][model_name]['acoes']['view'] = p

    return estrutura


@login_required
@permission_required('auth.view_group', raise_exception=True)
def lista_grupos(request):
    search = request.GET.get('search', '')

    # Adicionamos .select_related('detalhe') para carregar a descrição junto e ficar rápido
    grupos = Group.objects.all().annotate(
        total_usuarios=Count('user')
    ).select_related('detalhe').order_by('name')

    if search:
        grupos = grupos.filter(name__icontains=search)

    paginator = Paginator(grupos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Perfis de Acesso'
    }
    return render(request, 'usuarios/grupos/lista.html', context)


@login_required
@permission_required('auth.add_group', raise_exception=True)
def criar_grupo(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        descricao = request.POST.get('descricao')  # Pegamos a descrição
        permissoes_ids = request.POST.getlist('permissoes')

        if not name:
            messages.error(request, 'O nome do perfil é obrigatório.')
        else:
            try:
                grupo = Group.objects.create(name=name)

                # SALVAR DESCRIÇÃO: Criamos o detalhe vinculado ao grupo
                if descricao:
                    DetalheGrupo.objects.create(
                        group=grupo, descricao=descricao)

                if permissoes_ids:
                    perms = Permission.objects.filter(id__in=permissoes_ids)
                    grupo.permissions.set(perms)

                messages.success(request, 'Perfil criado com sucesso!')
                return redirect('usuarios:lista_grupos')
            except Exception as e:
                messages.error(request, f'Erro ao criar perfil: {e}')

    context = {
        'perms_agrupadas': agrupar_permissoes_para_template(),
        'title': 'Novo Perfil de Acesso'
    }
    return render(request, 'usuarios/grupos/form.html', context)


@login_required
@permission_required('auth.change_group', raise_exception=True)
def editar_grupo(request, pk):
    grupo = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name')
        descricao = request.POST.get('descricao')  # Pegamos a descrição
        permissoes_ids = request.POST.getlist('permissoes')

        if not name:
            messages.error(request, 'O nome do perfil é obrigatório.')
        else:
            try:
                grupo.name = name
                grupo.save()

                # SALVAR DESCRIÇÃO: Usamos update_or_create para criar se não existir ou atualizar se existir
                DetalheGrupo.objects.update_or_create(
                    group=grupo,
                    defaults={'descricao': descricao}
                )

                if permissoes_ids:
                    perms = Permission.objects.filter(id__in=permissoes_ids)
                    grupo.permissions.set(perms)
                else:
                    grupo.permissions.clear()

                messages.success(request, 'Perfil atualizado com sucesso!')
                return redirect('usuarios:lista_grupos')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar perfil: {e}')

    grupo_perms_ids = list(grupo.permissions.values_list('id', flat=True))

    context = {
        'grupo': grupo,
        'perms_agrupadas': agrupar_permissoes_para_template(),
        'grupo_perms_ids': grupo_perms_ids,
        'title': 'Editar Perfil de Acesso'
    }
    return render(request, 'usuarios/grupos/form.html', context)


def agrupar_permissoes_para_template():
    """
    Cria uma estrutura de dados aninhada e organizada para exibir as
    permissões no template, com overrides manuais para organização visual.
    """

    # 1. MAPEAMENTO DE NOMES AMIGÁVEIS (MODELO -> TELA)
    nomes_funcionalidades = {
        'pilar': 'Pilares',
        'categoriaauditoria': 'Categorias de Auditoria',
        'norma': 'Normas',
        'ferramentadigital': 'Ferramentas Digitais',
        'checklist': 'Checklists',
        'modeloauditoria': 'Modelos de Auditoria',
        'auditoria': 'Agendamentos',
        'auditoriainstancia': 'Execuções de Auditoria',
        'planodeacao': 'Planos de Ação',
        'naoconformidade': 'Não Conformidades',  # Movido para cá
        'usuario': 'Usuários',
        'group': 'Perfis de Acesso (Grupos)',
        'detalhegrupo': 'Detalhes do Grupo',
        'cliente': 'Clientes',
        'fornecedor': 'Fornecedores',
        'ativo': 'Ativos',
        'categoria': 'Categorias',
        'marca': 'Marcas',
        'modelo': 'Modelos',
        'item': 'Itens',
        'almoxarifado': 'Almoxarifados',
        'empresa': 'Unidades de Negócio',
        'area': 'Áreas',
        'setor': 'Setores',
        'subsetor': 'Subsetores',
        # Cadastros Base
        'turno': 'Turnos',
        'turnodetalhedia': 'Detalhes de Turno',
        'unidademedida': 'Unidades de Medida',
        'categoriaitem': 'Categorias',
        'subcategoriaitem': 'Subcategorias',
    }

    # 2. MAPEAMENTO DE NOMES DE MÓDULOS (APP -> TÍTULO DO ACCORDION)
    nomes_modulos = {
        'auditorias': 'Gestão de Auditorias',
        'usuarios': 'Gestão de Usuários',
        'organizacao': 'Estrutura Organizacional',
        'ativos': 'Gestão de Ativos',
        'itens': 'Estoque & Itens',
        'clientes': 'Gestão de Clientes',  # Se o app for 'clientes'
        'fornecedores': 'Gestão de Fornecedores',
        'cadastros_base': 'Cadastros Gerais',
        # Criamos uma chave "virtual" para o módulo novo
        'modulo_planos': 'Gestão de Planos de Ação',
        'auth': 'Grupos & Permissões',
    }

    # 3. LISTA NEGRA: O QUE NÃO DEVE APARECER NA TELA
    ignorar_apps = [
        'admin', 'authtoken', 'contenttypes', 'sessions',
        'easy_thumbnails', 'guardian', 'cadastros_base',  # Outros apps técnicos comuns
    ]

    # Adicione aqui os modelos estranhos que você quer esconder
    ignorar_modelos = [
        'log entry', 'permission', 'content type', 'session', 'admin log',
        'token', 'token proxy',
        # Modelos técnicos do plano de ação que você não quer ver:
        'forum', 'mensagemforum', 'responsavellocal', 'anexoresposta',
        'evidenciaplano', 'ferramentacausaraiz',
    ]

    # Busca as permissões no banco
    permissions = Permission.objects.select_related('content_type')\
        .exclude(content_type__app_label__in=ignorar_apps)\
        .exclude(content_type__model__in=ignorar_modelos)\
        .order_by('content_type__model')

    # Agrupa permissões por modelo
    perms_por_modelo = defaultdict(list)
    for perm in permissions:
        perms_por_modelo[perm.content_type.model].append(perm)

    # Estrutura final
    modulos = defaultdict(list)

    # 4. ORGANIZAÇÃO E LÓGICA DE OVERRIDE (AQUI ACONTECE A MÁGICA)
    for model_codename, perms in perms_por_modelo.items():
        if not perms:
            continue

        app_label = perms[0].content_type.app_label

        # --- LÓGICA DE OVERRIDE (MUDAR DE LUGAR) ---

        # Se for Plano de Ação ou Não Conformidade, forçamos ir para o módulo 'modulo_planos'
        if model_codename in ['planodeacao', 'naoconformidade']:
            chave_modulo = 'modulo_planos'
        else:
            chave_modulo = app_label

        # Pega o nome bonito do módulo ou usa o nome do app formatado
        modulo_nome = nomes_modulos.get(
            chave_modulo, chave_modulo.replace('_', ' ').title())

        # Pega o nome bonito da funcionalidade ou usa o nome do model formatado
        funcionalidade_nome = nomes_funcionalidades.get(
            model_codename, model_codename.replace('_', ' ').title())

        # Mapeia as ações
        acoes = {
            'add': next((p for p in perms if p.codename.startswith('add_')), None),
            'view': next((p for p in perms if p.codename.startswith('view_')), None),
            'change': next((p for p in perms if p.codename.startswith('change_')), None),
            'delete': next((p for p in perms if p.codename.startswith('delete_')), None),
        }

        # Só adiciona se tiver pelo menos uma ação válida
        if any(acoes.values()):
            modulos[modulo_nome].append({
                'nome': funcionalidade_nome,
                'acoes': acoes
            })

    # Ordena os módulos e as funcionalidades dentro deles
    modulos_ordenados = {
        k: sorted(v, key=lambda x: x['nome']) for k, v in sorted(modulos.items())
    }

    return modulos_ordenados


@login_required
@user_passes_test(admin_required)
def deletar_grupo(request, pk):
    """Deleta um grupo"""
    grupo = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        try:
            grupo.delete()
            messages.success(request, 'Grupo deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar grupo: {str(e)}')
        return redirect('usuarios:lista_grupos')

    context = {
        'grupo': grupo,
        'title': 'Deletar Grupo'
    }
    return render(request, 'usuarios/grupos/deletar.html', context)


# ============================================================================
# VIEWS AJAX E UTILITÁRIAS
# ============================================================================
@login_required
@user_passes_test(admin_required)
def exportar_usuarios_csv(request):
    """Exporta a lista de usuários filtrada para um arquivo CSV."""
    response = HttpResponse(
        content_type='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': 'attachment; filename="usuarios.csv"'}
    )

    # Reaplica a mesma lógica de filtro da view de listagem
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    grupo = request.GET.get('grupo', '')

    usuarios = Usuario.objects.prefetch_related('groups').all()

    if search:
        usuarios = usuarios.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    if status == 'ativo':
        usuarios = usuarios.filter(is_active=True)
    elif status == 'inativo':
        usuarios = usuarios.filter(is_active=False)
    elif status == 'staff':
        usuarios = usuarios.filter(is_staff=True)

    if grupo:
        usuarios = usuarios.filter(groups__id=grupo)

    usuarios = usuarios.order_by('username')

    # Cria o escritor CSV
    writer = csv.writer(response)

    # Escreve o cabeçalho
    writer.writerow([
        'ID',
        'Username',
        'Nome',
        'Sobrenome',
        'Email',
        'Ativo',
        'Staff',
        'Superusuário',
        'Grupos',
        'Data de Cadastro'
    ])

    # Escreve os dados de cada usuário no arquivo
    for usuario in usuarios:
        grupos_str = ', '.join([g.name for g in usuario.groups.all()])

        writer.writerow([
            usuario.id,
            usuario.username,
            usuario.first_name,
            usuario.last_name,
            usuario.email,
            'Sim' if usuario.is_active else 'Não',
            'Sim' if usuario.is_staff else 'Não',
            'Sim' if usuario.is_superuser else 'Não',
            grupos_str,
            usuario.date_joined.strftime('%d/%m/%Y %H:%M')
        ])

    return response


@require_http_methods(["GET"])
def verificar_username(request):
    """Verifica se um username está disponível"""
    username = request.GET.get('username')
    user_id = request.GET.get('user_id')

    if not username:
        return JsonResponse({'available': False, 'message': 'Username é obrigatório'})

    query = Usuario.objects.filter(username=username)
    if user_id:
        query = query.exclude(pk=user_id)

    if query.exists():
        return JsonResponse({'available': False, 'message': 'Este username já está em uso'})

    return JsonResponse({'available': True, 'message': 'Username disponível'})


@require_http_methods(["GET"])
def verificar_email(request):
    """Verifica se um email está disponível"""
    email = request.GET.get('email')
    user_id = request.GET.get('user_id')

    if not email:
        return JsonResponse({'available': False, 'message': 'Email é obrigatório'})

    query = Usuario.objects.filter(email=email)
    if user_id:
        query = query.exclude(pk=user_id)

    if query.exists():
        return JsonResponse({'available': False, 'message': 'Este email já está em uso'})

    return JsonResponse({'available': True, 'message': 'Email disponível'})


@require_http_methods(["POST"])
def toggle_usuario_status(request, pk):
    """Alterna o status ativo/inativo de um usuário"""
    usuario = get_object_or_404(Usuario, pk=pk)

    if usuario == request.user:
        return JsonResponse({'success': False, 'message': 'Você não pode desativar sua própria conta'})

    try:
        usuario.is_active = not usuario.is_active
        usuario.save()

        status_text = 'ativado' if usuario.is_active else 'desativado'
        return JsonResponse({
            'success': True,
            'message': f'Usuário {status_text} com sucesso',
            'new_status': usuario.is_active
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_http_methods(["POST"])
def bulk_action_usuarios(request):
    """Executa ações em lote nos usuários"""
    action = request.POST.get('action')
    user_ids = request.POST.getlist('user_ids')

    if not action or not user_ids:
        return JsonResponse({'success': False, 'message': 'Ação ou usuários não especificados'})

    try:
        usuarios = Usuario.objects.filter(
            id__in=user_ids).exclude(pk=request.user.pk)
        count = usuarios.count()

        if action == 'activate':
            usuarios.update(is_active=True)
            message = f'{count} usuário(s) ativado(s) com sucesso'
        elif action == 'deactivate':
            usuarios.update(is_active=False)
            message = f'{count} usuário(s) desativado(s) com sucesso'
        elif action == 'delete':
            usuarios.delete()
            message = f'{count} usuário(s) excluído(s) com sucesso'
        else:
            return JsonResponse({'success': False, 'message': 'Ação inválida'})

        return JsonResponse({'success': True, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# ============================================================================
# VIEWS PARA PERFIL DO USUÁRIO
# ============================================================================


@login_required
def meu_perfil(request):
    """Exibe e edita o perfil do usuário logado"""
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')

        try:
            request.user.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar perfil: {str(e)}')

    context = {
        'title': 'Meu Perfil'
    }
    return render(request, 'usuarios/perfil.html', context)


@login_required
def alterar_minha_senha(request):
    """Permite ao usuário alterar sua própria senha"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('usuarios:meu_perfil')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = PasswordChangeForm(request.user)

    context = {
        'form': form,
        'title': 'Alterar Senha'
    }
    return render(request, 'usuarios/alterar_minha_senha.html', context)


class CustomAuthToken(ObtainAuthToken):
    """
    View de login personalizada para retornar mais dados além do token.
    """

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        # Serializa os dados do usuário para incluir na resposta
        user_serializer = UsuarioSerializer(user)

        return Response({
            'token': token.key,
            'user': user_serializer.data
        })


class MeuPerfilAPIView(RetrieveUpdateAPIView):
    """
    Endpoint da API para ver e editar o perfil do usuário logado.
    Permite requisições GET (buscar) e PUT/PATCH (atualizar).
    """
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Retorna o objeto do próprio usuário que está fazendo a requisição.
        """
        return self.request.user


class AlterarMinhaSenhaAPIView(UpdateAPIView):
    """
    Endpoint para o usuário alterar a própria senha.
    """
    serializer_class = AlterarSenhaSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        usuario = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Senha alterada com sucesso!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
