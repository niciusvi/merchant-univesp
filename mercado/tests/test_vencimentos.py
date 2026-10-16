"""Testes das regras de vencimento (``mercado/vencimentos.py``).

A data de "hoje" é fixa (``HOJE``) e passada por parâmetro: o resultado não
muda conforme o dia em que a suíte roda.
"""

from datetime import date, timedelta

from django.test import SimpleTestCase, TestCase

from mercado import vencimentos
from mercado.models import Product, ProductBatch

HOJE = date(2026, 10, 16)


def criar_produto(nome: str, codigo: str) -> Product:
    return Product.objects.create(name=nome, barcode=codigo, price=1)


def criar_lote(
    produto: Product,
    dias_para_vencer: int | None,
    quantidade: int = 1,
    lote: str = "",
) -> ProductBatch:
    validade = (
        None if dias_para_vencer is None else HOJE + timedelta(days=dias_para_vencer)
    )
    return ProductBatch.objects.create(
        product=produto,
        batch_number=lote,
        expiration_date=validade,
        quantity=quantidade,
        purchase_price=1,
    )


class InterpretarFiltroDiasTest(SimpleTestCase):
    def test_vazio_usa_o_padrao(self) -> None:
        self.assertEqual(vencimentos.interpretar_filtro_dias(None), 7)
        self.assertEqual(vencimentos.interpretar_filtro_dias(""), 7)

    def test_aceita_cada_opcao_da_lista(self) -> None:
        for opcao in (3, 7, 15, 30):
            self.assertEqual(vencimentos.interpretar_filtro_dias(str(opcao)), opcao)

    def test_recusa_valor_fora_da_lista_explicando_o_esperado(self) -> None:
        with self.assertRaises(ValueError) as contexto:
            vencimentos.interpretar_filtro_dias("10")
        self.assertIn("'10'", str(contexto.exception))
        self.assertIn("(3, 7, 15, 30)", str(contexto.exception))

    def test_recusa_texto_e_numero_negativo(self) -> None:
        for invalido in ("abc", "-3", "3.5", " 7"):
            with self.assertRaises(ValueError):
                vencimentos.interpretar_filtro_dias(invalido)


class DescreverSituacaoTest(SimpleTestCase):
    def test_textos_por_faixa_de_dias(self) -> None:
        self.assertEqual(vencimentos.descrever_situacao(-1), "Vencido")
        self.assertEqual(vencimentos.descrever_situacao(0), "Vence hoje")
        self.assertEqual(vencimentos.descrever_situacao(1), "Vence amanhã")
        self.assertEqual(vencimentos.descrever_situacao(5), "Vence em 5 dias")

    def test_dias_restantes_negativo_quando_ja_venceu(self) -> None:
        self.assertEqual(vencimentos.dias_restantes(HOJE, HOJE + timedelta(days=2)), 2)
        self.assertEqual(vencimentos.dias_restantes(HOJE, HOJE - timedelta(days=1)), -1)


class LotesAVencerTest(TestCase):
    def setUp(self) -> None:
        leite = criar_produto("Leite", "1")
        pao = criar_produto("Pão", "2")
        criar_lote(leite, -1, quantidade=2, lote="VENCIDO")
        criar_lote(leite, 0, lote="HOJE")
        criar_lote(pao, 3, lote="D3")
        criar_lote(pao, 7, lote="D7")
        criar_lote(pao, 8, lote="D8")
        criar_lote(leite, 30, lote="D30")
        criar_lote(leite, 31, lote="D31")
        criar_lote(pao, None, lote="SEM-VALIDADE")
        criar_lote(pao, 2, quantidade=0, lote="ZERADO")

    def numeros_dos_lotes(self, dias: int) -> list[str]:
        return [linha.numero_lote for linha in vencimentos.lotes_a_vencer(HOJE, dias)]

    def test_janela_de_3_dias_inclui_vencidos_e_ordena_do_mais_urgente(self) -> None:
        self.assertEqual(self.numeros_dos_lotes(3), ["VENCIDO", "HOJE", "D3"])

    def test_janela_de_7_dias_inclui_o_limite_e_exclui_o_dia_seguinte(self) -> None:
        self.assertEqual(self.numeros_dos_lotes(7), ["VENCIDO", "HOJE", "D3", "D7"])

    def test_janela_de_30_dias_ignora_sem_validade_e_lotes_zerados(self) -> None:
        lotes = self.numeros_dos_lotes(30)
        self.assertIn("D30", lotes)
        for excluido in ("D31", "SEM-VALIDADE", "ZERADO"):
            self.assertNotIn(excluido, lotes)

    def test_linha_traz_dias_restantes_situacao_e_marca_de_vencido(self) -> None:
        primeira = vencimentos.lotes_a_vencer(HOJE, 3)[0]
        self.assertEqual(primeira.produto, "Leite")
        self.assertEqual(primeira.quantidade, 2)
        self.assertEqual(primeira.dias_restantes, -1)
        self.assertEqual(primeira.situacao, "Vencido")
        self.assertTrue(primeira.vencido)


class ResumirVencimentosTest(TestCase):
    def test_conta_produtos_vencidos_e_proximos_de_7_dias(self) -> None:
        leite = criar_produto("Leite", "1")
        criar_produto("Pão", "2")
        criar_lote(leite, -1, lote="VENCIDO")
        criar_lote(leite, 0, lote="HOJE")
        criar_lote(leite, 7, lote="D7")
        criar_lote(leite, 8, lote="D8")
        criar_lote(leite, -5, quantidade=0, lote="ZERADO")

        resumo = vencimentos.resumir_vencimentos(HOJE)

        self.assertEqual(resumo.total_produtos, 2)
        self.assertEqual(resumo.lotes_vencidos, 1)
        self.assertEqual(resumo.lotes_proximos, 2)
