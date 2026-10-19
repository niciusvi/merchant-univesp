"""Quem é usuário do mercado e quem é administrador.

Duas contas convivem no mesmo ``auth_user`` do Django:

- **conta técnica** (``is_superuser``/``is_staff``), criada por ``DJANGO_SUPERUSER_*``,
  só entra em ``/admin/``;
- **usuários do mercado**, com ``PerfilDeAcesso``, usam o painel; o papel de
  administrador está no perfil (``administrador=True``), nunca em ``is_superuser``.

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

from .models import PerfilDeAcesso


def perfil_do_mercado(
    usuario: AbstractBaseUser | AnonymousUser,
) -> PerfilDeAcesso | None:
    """Perfil do mercado do usuário, ou ``None`` (anônimo ou conta técnica).

    Exemplo: ``perfil_do_mercado(request.user)``.
    """
    # Sem perfil, o Django levanta RelatedObjectDoesNotExist (um AttributeError):
    # o getattr com padrão cobre esse caso e o do AnonymousUser.
    return getattr(usuario, "perfil_mercado", None)


def tem_acesso_ao_painel(usuario: AbstractBaseUser | AnonymousUser) -> bool:
    """``True`` só para usuário do mercado (com perfil)."""
    return perfil_do_mercado(usuario) is not None


def eh_administrador(usuario: AbstractBaseUser | AnonymousUser) -> bool:
    """``True`` para usuário do mercado com ``administrador=True`` no perfil.

    Exemplo: ``eh_administrador(request.user)``.
    """
    perfil = perfil_do_mercado(usuario)
    return perfil is not None and perfil.administrador


def exigir_administrador(
    view: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    """Decorator de view: responde 403 a quem não é administrador do mercado.

    403 e não redirecionamento para o login: a pessoa já está logada (o
    ``LoginRequiredMiddleware`` garante), só não tem o papel.
    """

    @wraps(view)
    def protegida(
        request: HttpRequest, *args: object, **kwargs: object
    ) -> HttpResponse:
        if not eh_administrador(request.user):
            raise PermissionDenied(
                "Apenas administradores do mercado gerenciam usuários."
            )
        return view(request, *args, **kwargs)

    return protegida
