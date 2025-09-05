# auditorias/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Auditoria


@login_required
def lista_auditorias(request):
    todas_auditorias = Auditoria.objects.all()
    context = {
        'todas_auditorias': todas_auditorias,
    }
    return render(request, 'lista_auditorias.html', context)
