"""Barreira entre o painel do mercado e o superusuário do Django.

O ``LoginRequiredMiddleware`` garante que há alguém logado. Este middleware
garante que esse alguém é **usuário do mercado** (tem ``PerfilDeAcesso``).
Quem entra com a conta técnica do Django (``/admin/``) não tem perfil e vê a
tela "sem acesso" em vez do painel; o contrário também vale, porque usuário
do mercado não é ``is_staff``.

Exemplo (settings)::

    MIDDLEWARE = [..., 'django.contrib.auth.middleware.LoginRequiredMiddleware',
                  'mercado.middleware.ExigirPerfilDoMercadoMiddleware', ...]
"""

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .autorizacao import tem_acesso_ao_painel


class ExigirPerfilDoMercadoMiddleware:
    """Responde 403 (tela amigável) a usuário logado sem perfil do mercado."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable[..., HttpResponse],
        view_args: tuple[object, ...],
        view_kwargs: dict[str, object],
    ) -> HttpResponse | None:
        if self._view_fica_fora_da_barreira(request, view_func):
            return None
        if tem_acesso_ao_painel(request.user):
            return None
        return render(request, "sem_acesso.html", status=403)

    @staticmethod
    def _view_fica_fora_da_barreira(
        request: HttpRequest, view_func: Callable[..., HttpResponse]
    ) -> bool:
        # Anônimo: o LoginRequiredMiddleware já cuida. Views marcadas com
        # @login_not_required (login, sair, redirecionamentos) e o /admin/
        # (que tem o próprio controle de staff) ficam de fora.
        if not request.user.is_authenticated:
            return True
        if getattr(view_func, "login_required", True) is False:
            return True
        resolvido = request.resolver_match
        return bool(resolvido and resolvido.app_name == "admin")
