"""Carga inicial do banco: os dados que já existiam no repositório original.

Idempotente: só carrega a fixture quando ainda não há produto algum. Assim o
script de entrada do contêiner pode chamá-lo a cada reinício sem duplicar nada.

Exemplo: ``python manage.py semear_dados_iniciais``.
"""

from typing import Any

from django.core.management import call_command
from django.core.management.base import BaseCommand

from mercado.models import Product

# Arquivo em mercado/fixtures/, exportado do db.sqlite3 que estava versionado.
NOME_FIXTURE = "dados_iniciais"


class Command(BaseCommand):
    help = "Carrega mercado/fixtures/dados_iniciais.json se o banco estiver vazio."

    def handle(self, *args: Any, **options: Any) -> None:
        if Product.objects.exists():
            self.stdout.write("Banco já tem produtos; carga inicial ignorada.")
            return
        call_command("loaddata", NOME_FIXTURE, verbosity=0)
        total = Product.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f"Carga inicial aplicada: {total} produto(s).")
        )
