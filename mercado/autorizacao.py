"""Quem pode administrar usuários.

Regra do projeto: só quem é administrador (``is_superuser``) cria usuários e
troca a senha dos outros. O primeiro administrador nasce das variáveis
``DJANGO_SUPERUSER_*`` (comando ``criar_admin_inicial``); os demais são
criados por ele na tela de usuários.

Exemplo::

    @exigir_administrador
    def listar_usuarios(request): ...
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse


def eh_administrador(usuario: AbstractBaseUser | AnonymousUser) -> bool:
    """``True`` para usuário logado marcado como ``is_superuser``.

    Exemplo: ``eh_administrador(request.user)``.
    """
    return bool(getattr(usuario, "is_superuser", False))


def exigir_administrador(
    view: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    """Decorator de view: responde 403 a quem não é administrador.

    403 e não redirecionamento para o login: a pessoa já está logada (o
    ``LoginRequiredMiddleware`` garante), só não tem o papel.
    Exemplo: ver docstring do módulo.
    """

    @wraps(view)
    def protegida(
        request: HttpRequest, *args: object, **kwargs: object
    ) -> HttpResponse:
        if not eh_administrador(request.user):
            raise PermissionDenied("Apenas administradores gerenciam usuários.")
        return view(request, *args, **kwargs)

    return protegida
