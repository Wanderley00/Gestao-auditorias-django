from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import Forum, MensagemForum
from django.utils import timezone
from datetime import timedelta
import json


@login_required
def api_listar_mensagens(request, forum_id):
    forum = get_object_or_404(Forum, pk=forum_id)
    mensagens = forum.mensagens.select_related(
        'autor').all().order_by('data_envio')

    data = []
    agora = timezone.now()

    for msg in mensagens:
        is_me = msg.autor == request.user

        # Verifica se passou menos de 1 hora (3600 segundos)
        tempo_decorrido = agora - msg.data_envio
        pode_editar = is_me and (tempo_decorrido.total_seconds() <= 3600)

        # Ajuste do fuso horário para exibição
        data_local = timezone.localtime(msg.data_envio)

        data.append({
            'id': msg.id,
            'autor': msg.autor.get_full_name() or msg.autor.username if msg.autor else 'Sistema',
            'conteudo': msg.conteudo,
            'data_envio': data_local.strftime('%d/%m %H:%M'),
            'is_me': is_me,
            'can_edit': pode_editar,  # <--- Nova flag para o frontend
            'editado': msg.editado,
        })

    return JsonResponse({'mensagens': data})


@login_required
@require_http_methods(["POST"])
def api_editar_mensagem(request, mensagem_id):
    """Edita uma mensagem se estiver dentro do prazo de 1 hora."""
    mensagem = get_object_or_404(
        MensagemForum, pk=mensagem_id, autor=request.user)

    # Validação de tempo no Backend (Segurança)
    agora = timezone.now()
    if (agora - mensagem.data_envio).total_seconds() > 3600:
        return JsonResponse({'success': False, 'error': 'Tempo limite para edição excedido.'}, status=403)

    try:
        data = json.loads(request.body)
        novo_conteudo = data.get('conteudo')

        if not novo_conteudo:
            return JsonResponse({'success': False, 'error': 'Conteúdo vazio.'})

        mensagem.conteudo = novo_conteudo
        mensagem.editado = True  # <--- ADICIONE ESTA LINHA: Marca como editado
        mensagem.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def api_deletar_mensagem(request, mensagem_id):
    """Deleta uma mensagem se estiver dentro do prazo de 1 hora."""
    mensagem = get_object_or_404(
        MensagemForum, pk=mensagem_id, autor=request.user)

    # Validação de tempo no Backend (Segurança)
    agora = timezone.now()
    if (agora - mensagem.data_envio).total_seconds() > 3600:
        return JsonResponse({'success': False, 'error': 'Tempo limite para exclusão excedido.'}, status=403)

    try:
        mensagem.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def api_enviar_mensagem(request, forum_id):
    """Recebe uma nova mensagem e salva no banco."""
    forum = get_object_or_404(Forum, pk=forum_id)

    try:
        data = json.loads(request.body)
        conteudo = data.get('conteudo')

        if not conteudo:
            return JsonResponse({'error': 'Conteúdo vazio'}, status=400)

        nova_mensagem = MensagemForum.objects.create(
            forum=forum,
            autor=request.user,
            conteudo=conteudo
        )

        return JsonResponse({
            'success': True,
            'mensagem': {
                'id': nova_mensagem.id,
                'autor': request.user.get_full_name() or request.user.username,
                'conteudo': nova_mensagem.conteudo,
                'data_envio': nova_mensagem.data_envio.strftime('%d/%m %H:%M'),
                'is_me': True
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
