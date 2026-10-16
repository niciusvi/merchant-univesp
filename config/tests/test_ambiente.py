"""Testes dos leitores de variáveis de ambiente (``config/ambiente.py``).

Cada teste troca o ambiente com ``patch.dict`` e o restaura ao sair: nenhum
teste enxerga o ``.env`` real da máquina.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config import ambiente

SEGREDO_FORTE = "a" * 50


class LerTextoTest(SimpleTestCase):
    def test_devolve_o_valor_sem_espacos_nas_pontas(self) -> None:
        with patch.dict(os.environ, {"X_TESTE": "  abc "}):
            self.assertEqual(ambiente.ler_texto("X_TESTE"), "abc")

    def test_usa_o_padrao_quando_vazia_ou_ausente(self) -> None:
        with patch.dict(os.environ, {"X_TESTE": ""}):
            self.assertEqual(ambiente.ler_texto("X_TESTE", padrao="p"), "p")
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(ambiente.ler_texto("X_TESTE", padrao="p"), "p")

    def test_obrigatoria_e_ausente_explica_como_corrigir(self) -> None:
        with (
            patch.dict(os.environ, {}, clear=True),
            self.assertRaises(ImproperlyConfigured) as contexto,
        ):
            ambiente.ler_texto("X_TESTE")
        self.assertIn("X_TESTE", str(contexto.exception))
        self.assertIn(".env.example", str(contexto.exception))


class LerBooleanoTest(SimpleTestCase):
    def test_aceita_formas_verdadeiras_e_falsas(self) -> None:
        for verdadeiro in ("1", "true", "SIM", " on "):
            with patch.dict(os.environ, {"X_TESTE": verdadeiro}):
                self.assertTrue(ambiente.ler_booleano("X_TESTE", padrao=False))
        for falso in ("0", "false", "nao", "OFF"):
            with patch.dict(os.environ, {"X_TESTE": falso}):
                self.assertFalse(ambiente.ler_booleano("X_TESTE", padrao=True))

    def test_vazio_usa_o_padrao(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(ambiente.ler_booleano("X_TESTE", padrao=True))

    def test_valor_desconhecido_e_recusado_com_o_valor_na_mensagem(self) -> None:
        with (
            patch.dict(os.environ, {"X_TESTE": "talvez"}),
            self.assertRaises(ImproperlyConfigured) as contexto,
        ):
            ambiente.ler_booleano("X_TESTE", padrao=False)
        self.assertIn("'talvez'", str(contexto.exception))


class LerListaTest(SimpleTestCase):
    def test_separa_por_virgula_ignorando_espacos_e_vazios(self) -> None:
        with patch.dict(os.environ, {"X_TESTE": " a, b,,c "}):
            self.assertEqual(ambiente.ler_lista("X_TESTE"), ["a", "b", "c"])

    def test_vazio_usa_o_padrao_como_lista_nova(self) -> None:
        with patch.dict(os.environ, {"X_TESTE": ""}):
            lista = ambiente.ler_lista("X_TESTE", padrao=("localhost",))
        self.assertEqual(lista, ["localhost"])
        lista.append("outro")  # não pode alterar o padrão compartilhado
        self.assertEqual(
            ambiente.ler_lista("X_TESTE", padrao=("localhost",)), ["localhost"]
        )


class ExigirSegredoForteTest(SimpleTestCase):
    def test_em_depuracao_aceita_qualquer_valor(self) -> None:
        self.assertEqual(ambiente.exigir_segredo_forte("K", "TROQUE", True), "TROQUE")

    def test_em_producao_recusa_exemplo_e_valor_curto_sem_vazar_o_valor(self) -> None:
        for fraco in ("TROQUE-ESTE-VALOR-" + "x" * 40, "curto"):
            with self.assertRaises(ImproperlyConfigured) as contexto:
                ambiente.exigir_segredo_forte("K", fraco, False)
            self.assertNotIn(fraco, str(contexto.exception))
            self.assertIn("conteúdo omitido", str(contexto.exception))

    def test_em_producao_aceita_segredo_longo(self) -> None:
        self.assertEqual(
            ambiente.exigir_segredo_forte("K", SEGREDO_FORTE, False), SEGREDO_FORTE
        )


class CarregarArquivoEnvTest(SimpleTestCase):
    def test_arquivo_inexistente_devolve_false_sem_erro(self) -> None:
        self.assertFalse(ambiente.carregar_arquivo_env(Path("/nao/existe/.env")))

    def test_preenche_apenas_o_que_nao_existe_no_ambiente(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / ".env"
            arquivo.write_text(
                "X_NOVA=do_arquivo\nX_JA_DEFINIDA=do_arquivo\n", encoding="utf-8"
            )
            with patch.dict(os.environ, {"X_JA_DEFINIDA": "do_sistema"}, clear=True):
                self.assertTrue(ambiente.carregar_arquivo_env(arquivo))
                self.assertEqual(os.environ["X_NOVA"], "do_arquivo")
                self.assertEqual(os.environ["X_JA_DEFINIDA"], "do_sistema")
