"""Testes das telas: painel inicial, vencimentos e coluna de validade no estoque.

As views usam a data real (``timezone.localdate()``), então aqui os lotes são
criados em relação a ela.
"""

from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from mercado.models import Product, ProductBatch


def criar_produto_com_lote(
    nome: str,
    codigo: str,
    validade: date | None,
    quantidade: int = 1,
) -> Product:
    produto = Product.objects.create(name=nome, barcode=codigo, price=1)
    ProductBatch.objects.create(
        product=produto,
        expiration_date=validade,
        quantity=quantidade,
        purchase_price=1,
    )
    return produto


class PainelViewTest(TestCase):
    def test_painel_e_a_raiz_e_as_telas_ficam_em_stock_e_scan(self) -> None:
        # Requisito do subdomínio: painel em /, inventário em /stock/, scanner em /scan/.
        self.assertEqual(reverse("painel"), "/")
        self.assertEqual(reverse("estoque"), "/stock/")
        self.assertEqual(reverse("scan"), "/scan/")
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_prefixo_antigo_mercado_redireciona_para_a_raiz(self) -> None:
        # Links antigos (Cloud Run, README do grupo) continuam funcionando.
        resposta = self.client.get("/mercado/vencimentos/?dias=3")
        self.assertRedirects(
            resposta,
            "/vencimentos/?dias=3",
            status_code=301,
            fetch_redirect_response=False,
        )
        self.assertRedirects(
            self.client.get("/mercado/"),
            "/",
            status_code=301,
            fetch_redirect_response=False,
        )

    def test_painel_tem_atalhos_para_estoque_vencimentos_e_scanner(self) -> None:
        resposta = self.client.get(reverse("painel"))
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "painel.html")
        for rota in ("estoque", "vencimentos", "scan"):
            self.assertContains(resposta, f'href="{reverse(rota)}"')

    def test_painel_conta_lotes_vencidos(self) -> None:
        ontem = timezone.localdate() - timedelta(days=1)
        criar_produto_com_lote("Iogurte", "1", ontem)
        resposta = self.client.get(reverse("painel"))
        self.assertEqual(resposta.context["resumo"].lotes_vencidos, 1)


class VencimentosViewTest(TestCase):
    def test_sem_parametro_usa_janela_de_7_dias(self) -> None:
        resposta = self.client.get(reverse("vencimentos"))
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "vencimentos.html")
        self.assertEqual(resposta.context["dias"], 7)

    def test_aceita_janela_de_30_dias(self) -> None:
        resposta = self.client.get(reverse("vencimentos"), {"dias": "30"})
        self.assertEqual(resposta.context["dias"], 30)

    def test_janela_fora_da_lista_devolve_400_com_explicacao(self) -> None:
        resposta = self.client.get(reverse("vencimentos"), {"dias": "10"})
        self.assertEqual(resposta.status_code, 400)
        self.assertContains(resposta, "Filtro de dias inválido", status_code=400)

    def test_lista_so_os_lotes_dentro_da_janela(self) -> None:
        hoje = timezone.localdate()
        criar_produto_com_lote("Queijo", "1", hoje + timedelta(days=2))
        criar_produto_com_lote("Arroz", "2", hoje + timedelta(days=20))

        em_3_dias = self.client.get(reverse("vencimentos"), {"dias": "3"})
        self.assertContains(em_3_dias, "Queijo")
        self.assertNotContains(em_3_dias, "Arroz")

        em_30_dias = self.client.get(reverse("vencimentos"), {"dias": "30"})
        self.assertContains(em_30_dias, "Arroz")


class EstoqueComValidadeTest(TestCase):
    def test_tabela_mostra_a_proxima_validade_ignorando_lotes_zerados(self) -> None:
        hoje = timezone.localdate()
        produto = criar_produto_com_lote("Leite", "1", hoje + timedelta(days=10))
        ProductBatch.objects.create(
            product=produto,
            expiration_date=hoje + timedelta(days=5),
            quantity=3,
            purchase_price=1,
        )
        ProductBatch.objects.create(
            product=produto,
            expiration_date=hoje + timedelta(days=1),
            quantity=0,
            purchase_price=1,
        )

        resposta = self.client.get(reverse("estoque"))

        self.assertContains(resposta, "Próxima validade")
        self.assertContains(resposta, (hoje + timedelta(days=5)).strftime("%d/%m/%Y"))
        self.assertNotContains(
            resposta, (hoje + timedelta(days=1)).strftime("%d/%m/%Y")
        )

    def test_produto_sem_validade_mostra_traco(self) -> None:
        # Marca preenchida para que o único traço da linha seja o da validade.
        produto = Product.objects.create(
            name="Sal", barcode="1", brand="Cisne", price=1
        )
        ProductBatch.objects.create(
            product=produto, expiration_date=None, quantity=2, purchase_price=1
        )

        resposta = self.client.get(reverse("estoque"))

        self.assertContains(resposta, "—", count=1)
