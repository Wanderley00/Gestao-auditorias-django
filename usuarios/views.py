# usuarios/views.py

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
import json

from .serializers import UsuarioSerializer

from .models import Usuario

from .serializers import AlterarSenhaSerializer

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
@user_passes_test(admin_required)
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
@user_passes_test(admin_required)
def alterar_senha_usuario(request, pk):
    """Altera a senha de um usuário específico"""
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
@user_passes_test(admin_required)
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
        'create_url': 'usuarios:criar_usuario',  # <-- Chave que faltava
        'artigo': 'o'
    }
    return render(request, 'usuarios/lista.html', context)


@login_required
@user_passes_test(admin_required)
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
        grupos_ids = request.POST.getlist('grupos')

        # Validações
        if not username or not email or not password:
            messages.error(
                request, 'Username, email e senha são obrigatórios!')
        elif password != password_confirm:
            messages.error(request, 'As senhas não coincidem!')
        elif Usuario.objects.filter(username=username).exists():
            messages.error(request, 'Este username já está em uso!')
        elif Usuario.objects.filter(email=email).exists():
            messages.error(request, 'Este email já está em uso!')
        else:
            try:
                usuario = Usuario.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=is_active,
                    is_staff=is_staff,
                    is_superuser=is_superuser
                )

                # Adicionar aos grupos
                if grupos_ids:
                    usuario.groups.set(grupos_ids)

                messages.success(request, 'Usuário criado com sucesso!')
                return redirect('usuarios:lista_usuarios')
            except Exception as e:
                messages.error(request, f'Erro ao criar usuário: {str(e)}')

    context = {
        'grupos': Group.objects.all(),
        'title': 'Criar Usuário'
    }
    return render(request, 'usuarios/form.html', context)


@login_required
@user_passes_test(admin_required)
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
        grupos_ids = request.POST.getlist('grupos')

        # Validar username único (exceto o próprio usuário)
        if Usuario.objects.filter(username=usuario.username).exclude(pk=pk).exists():
            messages.error(request, 'Este username já está em uso!')
        # Validar email único (exceto o próprio usuário)
        elif Usuario.objects.filter(email=usuario.email).exclude(pk=pk).exists():
            messages.error(request, 'Este email já está em uso!')
        else:
            try:
                usuario.save()
                usuario.groups.set(grupos_ids)
                messages.success(request, 'Usuário atualizado com sucesso!')
                return redirect('usuarios:lista_usuarios')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar usuário: {str(e)}')

    context = {
        'usuario': usuario,
        'grupos': Group.objects.all(),
        'title': 'Editar Usuário'
    }
    return render(request, 'usuarios/form.html', context)


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


@login_required
@user_passes_test(admin_required)
def alterar_senha_usuario(request, pk):
    """Altera a senha de um usuário"""
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        nova_senha = request.POST.get('nova_senha')
        confirmar_senha = request.POST.get('confirmar_senha')

        if not nova_senha:
            messages.error(request, 'Nova senha é obrigatória!')
        elif nova_senha != confirmar_senha:
            messages.error(request, 'As senhas não coincidem!')
        elif len(nova_senha) < 8:
            messages.error(
                request, 'A senha deve ter pelo menos 8 caracteres!')
        else:
            try:
                usuario.set_password(nova_senha)
                usuario.save()
                messages.success(request, 'Senha alterada com sucesso!')
                return redirect('usuarios:lista_usuarios')
            except Exception as e:
                messages.error(request, f'Erro ao alterar senha: {str(e)}')

    context = {
        'usuario': usuario,
        'title': 'Alterar Senha'
    }
    return render(request, 'usuarios/alterar_senha.html', context)


# ============================================================================
# VIEWS PARA GRUPOS E PERMISSÕES
# ============================================================================

@login_required
@user_passes_test(admin_required)
def lista_grupos(request):
    """Lista todos os grupos"""
    search = request.GET.get('search', '')
    grupos = Group.objects.all()

    if search:
        grupos = grupos.filter(name__icontains=search)

    paginator = Paginator(grupos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Grupos'
    }
    return render(request, 'usuarios/grupos/lista.html', context)


@login_required
@user_passes_test(admin_required)
def criar_grupo(request):
    """Cria um novo grupo"""
    if request.method == 'POST':
        name = request.POST.get('name')
        permissoes_ids = request.POST.getlist('permissions')

        if not name:
            messages.error(request, 'Nome do grupo é obrigatório!')
        elif Group.objects.filter(name=name).exists():
            messages.error(request, 'Este nome de grupo já existe!')
        else:
            try:
                grupo = Group.objects.create(name=name)
                if permissoes_ids:
                    grupo.permissions.set(permissoes_ids)

                messages.success(request, 'Grupo criado com sucesso!')
                return redirect('usuarios:lista_grupos')
            except Exception as e:
                messages.error(request, f'Erro ao criar grupo: {str(e)}')

    # Organizar permissões por app
    permissoes_por_app = {}
    for permission in Permission.objects.select_related('content_type').all():
        app_label = permission.content_type.app_label
        if app_label not in permissoes_por_app:
            permissoes_por_app[app_label] = []
        permissoes_por_app[app_label].append(permission)

    context = {
        'permissoes_por_app': permissoes_por_app,
        'title': 'Criar Grupo'
    }
    return render(request, 'usuarios/grupos/form.html', context)


@login_required
@user_passes_test(admin_required)
def editar_grupo(request, pk):
    """Edita um grupo existente"""
    grupo = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        grupo.name = request.POST.get('name')
        permissoes_ids = request.POST.getlist('permissions')

        if not grupo.name:
            messages.error(request, 'Nome do grupo é obrigatório!')
        elif Group.objects.filter(name=grupo.name).exclude(pk=pk).exists():
            messages.error(request, 'Este nome de grupo já existe!')
        else:
            try:
                grupo.save()
                grupo.permissions.set(permissoes_ids)
                messages.success(request, 'Grupo atualizado com sucesso!')
                return redirect('usuarios:lista_grupos')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar grupo: {str(e)}')

    # Organizar permissões por app
    permissoes_por_app = {}
    for permission in Permission.objects.select_related('content_type').all():
        app_label = permission.content_type.app_label
        if app_label not in permissoes_por_app:
            permissoes_por_app[app_label] = []
        permissoes_por_app[app_label].append(permission)

    context = {
        'grupo': grupo,
        'permissoes_por_app': permissoes_por_app,
        'title': 'Editar Grupo'
    }
    return render(request, 'usuarios/grupos/form.html', context)


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
