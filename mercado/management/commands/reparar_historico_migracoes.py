"""Alinha o histórico de migrações de bancos criados antes da reorganização do grupo.

Em 16/10/2026 duas correções diferentes para o mesmo conflito conviveram:

- este fork aplicava ``0005_product_min_quantity_cashmovement`` + ``0007_merge_...``;
- o repositório do grupo renomeou aquela migração para ``0007_cashmovement`` e
  criou ``0008_product_min_quantity``.

O banco resultante é **idêntico** nos dois caminhos (tabela ``CashMovement`` e
coluna ``min_quantity`` existem). Só a tabela ``django_migrations`` guarda nomes
diferentes. Sem este reparo, ``migrate`` tentaria criar a tabela e a coluna de
novo e falharia com "already exists". Idempotente: roda a cada subida.

Exemplo: ``python manage.py reparar_historico_migracoes`` (antes do ``migrate``).
"""

from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

APP = "mercado"
NOME_ANTIGO_CAIXA = "0005_product_min_quantity_cashmovement"
NOME_NOVO_CAIXA = "0007_cashmovement"
NOME_MERGE_ANTIGO = "0007_merge_0005_caixa_0006_lotes_opcionais"
NOME_MIN_QUANTITY = "0008_product_min_quantity"


def renomear_registro(recorder: MigrationRecorder, antigo: str, novo: str) -> bool:
    """Troca o nome de uma migração já aplicada; devolve ``True`` se mexeu.

    Exemplo: ``renomear_registro(recorder, NOME_ANTIGO_CAIXA, NOME_NOVO_CAIXA)``.
    """
    aplicadas = recorder.applied_migrations()
    if (APP, antigo) not in aplicadas:
        return False
    recorder.record_unapplied(APP, antigo)
    if (APP, novo) not in aplicadas:
        recorder.record_applied(APP, novo)
    return True


def remover_registro(recorder: MigrationRecorder, nome: str) -> bool:
    """Apaga o registro de uma migração que deixou de existir; ``True`` se mexeu."""
    if (APP, nome) not in recorder.applied_migrations():
        return False
    recorder.record_unapplied(APP, nome)
    return True


class Command(BaseCommand):
    help = (
        "Renomeia no histórico as migrações da API para os nomes adotados pelo grupo."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        recorder = MigrationRecorder(connection)
        if not recorder.has_table():
            self.stdout.write("Banco novo: nada a reparar.")
            return
        mexeu = renomear_registro(recorder, NOME_ANTIGO_CAIXA, NOME_NOVO_CAIXA)
        if remover_registro(recorder, NOME_MERGE_ANTIGO):
            # A coluna min_quantity veio junto com a 0005 antiga: já existe.
            if (APP, NOME_MIN_QUANTITY) not in recorder.applied_migrations():
                recorder.record_applied(APP, NOME_MIN_QUANTITY)
            mexeu = True
        situacao = (
            "Histórico de migrações reparado."
            if mexeu
            else "Histórico já estava alinhado."
        )
        self.stdout.write(self.style.SUCCESS(situacao) if mexeu else situacao)
