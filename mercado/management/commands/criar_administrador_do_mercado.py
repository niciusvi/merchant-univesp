"""Cria o primeiro administrador do **mercado** a partir de ``MERCADO_ADMIN_USUARIO``
e ``MERCADO_ADMIN_SENHA``.

É uma conta diferente da técnica do Django (``DJANGO_SUPERUSER_*``, só para
``/admin/``): não é staff nem superuser, e tem ``PerfilDeAcesso`` com
``administrador=True``. Idempotente: se o usuário já existe, nada muda.

Exemplo: ``python manage.py criar_administrador_do_mercado`` com as variáveis no ambiente.
"""

import os
from typing import Any

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from mercado.models import PerfilDeAcesso


def credenciais_do_mercado() -> tuple[str, str]:
    """Devolve (usuário, senha) de ``MERCADO_ADMIN_USUARIO``/``MERCADO_ADMIN_SENHA``."""
    return (
        os.environ.get("MERCADO_ADMIN_USUARIO", "").strip(),
        os.environ.get("MERCADO_ADMIN_SENHA", ""),
    )


class Command(BaseCommand):
    help = "Cria o administrador do mercado se MERCADO_ADMIN_* estiverem definidas e ele não existir."

    def handle(self, *args: Any, **options: Any) -> None:
        usuario, senha = credenciais_do_mercado()
        if not usuario or not senha:
            self.stdout.write(
                "MERCADO_ADMIN_USUARIO/SENHA vazias; administrador do mercado não criado."
            )
            return
        if User.objects.filter(username=usuario).exists():
            self.stdout.write(f"Usuário {usuario!r} já existe; nada a fazer.")
            return
        criado = User.objects.create_user(username=usuario, password=senha)
        PerfilDeAcesso.objects.create(usuario=criado, administrador=True)
        self.stdout.write(
            self.style.SUCCESS(f"Administrador do mercado {usuario!r} criado.")
        )
