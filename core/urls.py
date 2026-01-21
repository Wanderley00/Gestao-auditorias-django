# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

# Importe as views da API diretamente
from usuarios.views import CustomAuthToken, MeuPerfilAPIView, AlterarMinhaSenhaAPIView
from auditorias.views import (
    AuditoriasPendentesAPIView,
    AuditoriasConcluidasAPIView,
    AuditoriaInstanciaDetailAPIView,
    SubmeterAuditoriaAPIView,
    LocaisPermitidosAPIView,
    AuditoriasQuarentenaAPIView,
)


def redirect_to_auditorias(request):
    return redirect('auditorias:dashboard')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_auditorias, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        http_method_names=['get', 'post']), name='logout'),
    path('auditorias/', include('auditorias.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('itens/', include('itens.urls')),
    path('ativos/', include('ativos.urls')),
    path('organizacao/', include('organizacao.urls')),
    # <-- ADICIONE ESTA LINHA
    path('clientes/', include('clientes.urls')),
    # <-- ADICIONE ESTA LINHA
    path('fornecedores/', include('fornecedores.urls')),

    path('planos_de_acao/', include('planos_de_acao.urls')),

    # URLs DA API E DOCUMENTAÇÃO
    # ============================================================================
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Interface Swagger UI:
    path('api/schema/swagger-ui/',
         SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Interface Redoc:
    path('api/schema/redoc/',
         SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# URLs da API centralizadas
api_urlpatterns = [
    # Autenticação e Usuário
    path('login/', CustomAuthToken.as_view(), name='api_login'),
    path('meu-perfil/', MeuPerfilAPIView.as_view(), name='api_meu_perfil'),
    path('alterar-minha-senha/', AlterarMinhaSenhaAPIView.as_view(),
         name='api_alterar_minha_senha'),

    # Auditorias
    path('auditorias/pendentes/', AuditoriasPendentesAPIView.as_view(),
         name='api_auditorias_pendentes'),
    path('auditorias/quarentena/', AuditoriasQuarentenaAPIView.as_view(),
         name='api_auditorias_quarentena'),
    path('auditorias/concluidas/', AuditoriasConcluidasAPIView.as_view(),
         name='api_auditorias_concluidas'),
    path('instancias/<int:pk>/', AuditoriaInstanciaDetailAPIView.as_view(),
         name='api_instancia_detail'),
    path('instancias/<int:pk>/locais-permitidos/', LocaisPermitidosAPIView.as_view(),
         name='api_instancia_locais'),
    path('instancias/<int:pk>/submeter/',
         SubmeterAuditoriaAPIView.as_view(), name='api_instancia_submeter'),


]


# URLs da Documentação
schema_urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/',
         SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# Adiciona os blocos de URLs da API e Documentação ao urlpatterns principal
urlpatterns += [
    path('api/', include(api_urlpatterns)),
    path('api/', include(schema_urlpatterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
