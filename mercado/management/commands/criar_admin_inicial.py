"""Cria o superusuário do admin a partir de ``DJANGO_SUPERUSER_USERNAME/PASSWORD/EMAIL``.

Diferente do ``createsuperuser --noinput`` do Django, não falha se o usuário já
existe nem se as variáveis estão vazias: avisa e segue. Por isso pode rodar a
cada subida do contêiner. A senha nunca é escrita na saída.

Exemplo: ``python manage.py criar_admin_inicial`` com as variáveis no ambiente.
"""

import os
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


def credenciais_do_ambiente() -> tuple[str, str, str]:
    """Devolve (usuário, senha, e-mail) lidos do ambiente, já sem espaços nas pontas.

    Exemplo: ``usuario, senha, email = credenciais_do_ambiente()``.
    """
    return (
        os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip(),
        os.environ.get("DJANGO_SUPERUSER_PASSWORD", ""),
        os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip(),
    )


class Command(BaseCommand):
    help = "Cria o admin inicial se DJANGO_SUPERUSER_* estiverem definidas e ele não existir."

    def handle(self, *args: Any, **options: Any) -> None:
        usuario, senha, email = credenciais_do_ambiente()
        if not usuario or not senha:
            self.stdout.write(
                "DJANGO_SUPERUSER_USERNAME/PASSWORD vazias; admin não criado."
            )
            return
        Usuario = get_user_model()
        if Usuario.objects.filter(username=usuario).exists():
            self.stdout.write(f"Usuário {usuario!r} já existe; nada a fazer.")
            return
        Usuario.objects.create_superuser(username=usuario, password=senha, email=email)
        self.stdout.write(self.style.SUCCESS(f"Admin {usuario!r} criado."))
