"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    # O app responde na raiz do subdomínio: painel em /, inventário em /stock/,
    # scanner em /scan/. O prefixo antigo /mercado/... redireciona (301) para os
    # links do Cloud Run e do README do grupo continuarem valendo.
    path('mercado/', RedirectView.as_view(url='/', permanent=True, query_string=True)),
    path(
        'mercado/<path:resto>',
        RedirectView.as_view(url='/%(resto)s', permanent=True, query_string=True),
    ),
    path('', include('mercado.urls')),
]
