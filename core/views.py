# core/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from auditorias.models import Auditoria, AuditoriaInstancia


@login_required
def home(request):
    # Contagem de auditorias agendadas
    total_auditorias = Auditoria.objects.count()
    auditorias_agendadas = Auditoria.objects.filter(
        data_inicio__gt=timezone.now()).count()
    auditorias_executadas = AuditoriaInstancia.objects.filter(
        executada=True).count()

    context = {
        'total_auditorias': total_auditorias,
        'auditorias_agendadas': auditorias_agendadas,
        'auditorias_executadas': auditorias_executadas,
    }
    return render(request, 'home.html', context)


def lista_auditorias(request):
    todas_auditorias = Auditoria.objects.all()
    context = {
        'todas_auditorias': todas_auditorias,
    }
    return render(request, 'lista_auditorias.html', context)
