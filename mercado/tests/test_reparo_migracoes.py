"""Reparo do histórico de migrações (``reparar_historico_migracoes``).

Simula um banco criado por este fork antes de o grupo renomear as migrações:
o esquema é o mesmo, só os nomes em ``django_migrations`` diferem.
"""

from io import StringIO

from django.core.management import call_command
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from django.test import TestCase

APP = "mercado"
ANTIGAS = (
    "0005_product_min_quantity_cashmovement",
    "0007_merge_0005_caixa_0006_lotes_opcionais",
)
NOVAS = ("0007_cashmovement", "0008_product_min_quantity")


def nomes_aplicados() -> set[str]:
    return {
        nome
        for app, nome in MigrationRecorder(connection).applied_migrations()
        if app == APP
    }


def simular_historico_antigo() -> None:
    recorder = MigrationRecorder(connection)
    for nova in NOVAS:
        recorder.record_unapplied(APP, nova)
    for antiga in ANTIGAS:
        recorder.record_applied(APP, antiga)


class RepararHistoricoMigracoesTest(TestCase):
    def test_troca_os_nomes_antigos_pelos_do_grupo(self) -> None:
        simular_historico_antigo()
        self.assertTrue(set(ANTIGAS) <= nomes_aplicados())

        saida = StringIO()
        call_command("reparar_historico_migracoes", stdout=saida)

        aplicadas = nomes_aplicados()
        self.assertTrue(set(NOVAS) <= aplicadas)
        self.assertFalse(set(ANTIGAS) & aplicadas)
        self.assertIn("reparado", saida.getvalue())

    def test_banco_ja_alinhado_nao_muda_nada(self) -> None:
        antes = nomes_aplicados()
        saida = StringIO()
        call_command("reparar_historico_migracoes", stdout=saida)
        self.assertEqual(nomes_aplicados(), antes)
        self.assertIn("alinhado", saida.getvalue())

    def test_rodar_duas_vezes_da_no_mesmo(self) -> None:
        simular_historico_antigo()
        call_command("reparar_historico_migracoes", stdout=StringIO())
        depois_da_primeira = nomes_aplicados()
        call_command("reparar_historico_migracoes", stdout=StringIO())
        self.assertEqual(nomes_aplicados(), depois_da_primeira)
