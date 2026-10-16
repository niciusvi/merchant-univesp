"""Garante que modelos e migrações estão sincronizados.

Regressão para a ``main`` de 16/10/2026: havia duas migrações ``0005`` (ramo da
API x ramo das telas) e o ``ProductBatch`` definido duas vezes em ``models.py``.
Qualquer um dos dois problemas faz ``makemigrations --check`` falhar.
"""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class MigracoesSincronizadasTest(TestCase):
    def test_makemigrations_check_nao_encontra_pendencias_nem_conflitos(self) -> None:
        # Conflito de ramos -> CommandError; migração faltando -> SystemExit(1).
        call_command(
            "makemigrations",
            "mercado",
            "--check",
            "--dry-run",
            stdout=StringIO(),
            stderr=StringIO(),
        )
