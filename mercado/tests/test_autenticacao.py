"""Login obrigatório em todas as telas e na API; entrar, sair e trocar a própria senha."""

from django.test import TestCase
from django.urls import reverse

from mercado.tests.apoio import SENHA_DE_TESTE, criar_usuario, entrar_como_usuario

OUTRA_SENHA = "outra-senha-forte-456"


class LoginObrigatorioTest(TestCase):
    def test_anonimo_vai_para_o_login_e_volta_depois(self) -> None:
        resposta = self.client.get(reverse("estoque"))
        destino = f"{reverse('entrar')}?next={reverse('estoque')}"
        self.assertRedirects(resposta, destino, fetch_redirect_response=False)

    def test_api_tambem_exige_login(self) -> None:
        self.assertEqual(self.client.get("/api/estoque/").status_code, 302)

    def test_tela_de_login_e_o_healthcheck_abrem_sem_sessao(self) -> None:
        resposta = self.client.get(reverse("entrar"))
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "login.html")

    def test_prefixo_antigo_redireciona_mesmo_sem_login(self) -> None:
        resposta = self.client.get("/mercado/stock/")
        self.assertRedirects(
            resposta, "/stock/", status_code=301, fetch_redirect_response=False
        )


class EntrarESairTest(TestCase):
    def setUp(self) -> None:
        self.usuario = criar_usuario("joana")

    def entrar(self, senha: str, **extras: str):
        dados = {"username": "joana", "password": senha, **extras}
        return self.client.post(reverse("entrar"), dados)

    def test_senha_errada_mostra_erro_e_nao_loga(self) -> None:
        resposta = self.entrar("errada")
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Usuário ou senha inválidos")
        self.assertFalse(resposta.wsgi_request.user.is_authenticated)

    def test_senha_certa_leva_ao_painel(self) -> None:
        self.assertRedirects(self.entrar(SENHA_DE_TESTE), reverse("painel"))

    def test_next_devolve_a_tela_que_a_pessoa_queria(self) -> None:
        resposta = self.entrar(SENHA_DE_TESTE, next="/stock/")
        self.assertRedirects(resposta, "/stock/")

    def test_usuario_desativado_nao_entra(self) -> None:
        self.usuario.is_active = False
        self.usuario.save(update_fields=["is_active"])
        resposta = self.entrar(SENHA_DE_TESTE)
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(resposta.wsgi_request.user.is_authenticated)

    def test_sair_exige_post_e_encerra_a_sessao(self) -> None:
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse("sair")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("sair")), reverse("entrar"))
        self.assertEqual(self.client.get(reverse("painel")).status_code, 302)


class MinhaSenhaTest(TestCase):
    def test_usuario_troca_a_propria_senha_informando_a_atual(self) -> None:
        usuario = entrar_como_usuario(self.client)
        dados = {
            "old_password": SENHA_DE_TESTE,
            "new_password1": OUTRA_SENHA,
            "new_password2": OUTRA_SENHA,
        }
        resposta = self.client.post(reverse("senha_propria"), dados)
        self.assertRedirects(resposta, reverse("painel"))
        usuario.refresh_from_db()
        self.assertTrue(usuario.check_password(OUTRA_SENHA))

    def test_senha_atual_errada_nao_troca(self) -> None:
        usuario = entrar_como_usuario(self.client)
        dados = {
            "old_password": "errada",
            "new_password1": OUTRA_SENHA,
            "new_password2": OUTRA_SENHA,
        }
        self.assertEqual(
            self.client.post(reverse("senha_propria"), dados).status_code, 200
        )
        usuario.refresh_from_db()
        self.assertTrue(usuario.check_password(SENHA_DE_TESTE))
