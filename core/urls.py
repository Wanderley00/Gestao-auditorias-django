# projeto_principal/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views

# View para redirecionar a raiz para auditorias
def redirect_to_auditorias(request):
    return redirect('auditorias:dashboard')

urlpatterns = [
    # Admin do Django
    path('admin/', admin.site.urls),
    
    # Redirecionamento da raiz
    path('', redirect_to_auditorias, name='home'),
    
    # Autenticação
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Apps principais
    path('auditorias/', include('auditorias.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('itens/', include('itens.urls')), # <-- ADICIONADO
    
    # Outras funcionalidades (para expansão futura)
    # path('relatorios/', include('relatorios.urls')),
    # path('configuracoes/', include('configuracoes.urls')),
]

# Servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

