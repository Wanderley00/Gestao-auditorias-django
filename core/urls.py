# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views

def redirect_to_auditorias(request):
    return redirect('auditorias:dashboard')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_auditorias, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(http_method_names=['get', 'post']), name='logout'),
    path('auditorias/', include('auditorias.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('itens/', include('itens.urls')),
    path('ativos/', include('ativos.urls')),
    path('organizacao/', include('organizacao.urls')), # <-- ADICIONE ESTA LINHA
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)