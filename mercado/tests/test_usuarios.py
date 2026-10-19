"""Gestão de usuários: só administrador cria, redefine senha e desativa."""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from mercado.tests.apoio import (
    SENHA_DE_TESTE,
    criar_superusuario_django,
    criar_usuario,
    entrar_como_usuario,
)

NOVA_SENHA = "senha-nova-bem-forte-789"


class UsuarioComumTest(TestCase):
    def setUp(self) -> None:
        entrar_como_usuario(self.client)

    def test_nao_ve_o_link_nem_acessa_as_telas_de_usuarios(self) -> None:
        self.assertNotContains(self.client.get(reverse("painel")), reverse("usuarios"))
        self.assertEqual(self.client.get(reverse("usuarios")).status_code, 403)
        dados = {
            "username": "intruso",
            "password1": NOVA_SENHA,
            "password2": NOVA_SENHA,
        }
        self.assertEqual(
            self.client.post(reverse("usuario_novo"), dados).status_code, 403
        )
        self.assertFalse(User.objects.filter(username="intruso").exists())


class AdministradorTest(TestCase):
    def setUp(self) -> None:
        self.admin = entrar_como_usuario(self.client, administrador=True)
        self.joana = criar_usuario("joana")

    def test_ve_o_link_e_a_lista_de_usuarios(self) -> None:
        self.assertContains(self.client.get(reverse("painel")), reverse("usuarios"))
        resposta = self.client.get(reverse("usuarios"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "joana")

    def test_cria_usuario_comum_que_consegue_entrar(self) -> None:
        dados = {"username": "carlos", "password1": NOVA_SENHA, "password2": NOVA_SENHA}
        resposta = self.client.post(reverse("usuario_novo"), dados)
        self.assertRedirects(resposta, reverse("usuarios"))
        carlos = User.objects.get(username="carlos")
        self.assertFalse(carlos.is_superuser)
        self.assertFalse(carlos.is_staff)
        self.assertFalse(carlos.perfil_mercado.administrador)
        self.assertIsNotNone(authenticate(username="carlos", password=NOVA_SENHA))

    def test_cria_outro_administrador_quando_marcado(self) -> None:
        dados = {
            "username": "socia",
            "password1": NOVA_SENHA,
            "password2": NOVA_SENHA,
            "administrador": "on",
        }
        self.client.post(reverse("usuario_novo"), dados)
        socia = User.objects.get(username="socia")
        # Administrador do MERCADO: papel no perfil, sem poderes no /admin/ do Django.
        self.assertTrue(socia.perfil_mercado.administrador)
        self.assertFalse(socia.is_superuser)
        self.assertFalse(socia.is_staff)

    def test_senhas_diferentes_nao_criam_usuario(self) -> None:
        dados = {
            "username": "carlos",
            "password1": NOVA_SENHA,
            "password2": "diferente-123456",
        }
        resposta = self.client.post(reverse("usuario_novo"), dados)
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(User.objects.filter(username="carlos").exists())

    def test_define_nova_senha_de_outro_usuario_sem_saber_a_atual(self) -> None:
        url = reverse("usuario_senha", kwargs={"usuario_id": self.joana.id})
        dados = {"new_password1": NOVA_SENHA, "new_password2": NOVA_SENHA}
        self.assertRedirects(self.client.post(url, dados), reverse("usuarios"))
        self.assertIsNotNone(authenticate(username="joana", password=NOVA_SENHA))
        self.assertIsNone(authenticate(username="joana", password=SENHA_DE_TESTE))

    def test_desativa_e_reativa_sem_apagar(self) -> None:
        url = reverse("usuario_ativo", kwargs={"usuario_id": self.joana.id})
        self.client.post(url)
        self.joana.refresh_from_db()
        self.assertFalse(self.joana.is_active)
        self.assertIsNone(authenticate(username="joana", password=SENHA_DE_TESTE))
        self.client.post(url)
        self.joana.refresh_from_db()
        self.assertTrue(self.joana.is_active)

    def test_nao_desativa_a_si_mesmo(self) -> None:
        url = reverse("usuario_ativo", kwargs={"usuario_id": self.admin.id})
        resposta = self.client.post(url, follow=True)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertContains(resposta, "não pode desativar a si mesmo")

    def test_desativar_exige_post(self) -> None:
        url = reverse("usuario_ativo", kwargs={"usuario_id": self.joana.id})
        self.assertEqual(self.client.get(url).status_code, 405)


class ContaTecnicaForaDaGestaoTest(TestCase):
    def setUp(self) -> None:
        entrar_como_usuario(self.client, administrador=True)
        self.tecnico = criar_superusuario_django()

    def test_conta_tecnica_nao_aparece_na_lista(self) -> None:
        self.assertNotContains(
            self.client.get(reverse("usuarios")), self.tecnico.username
        )

    def test_conta_tecnica_nao_e_editavel_pelo_painel(self) -> None:
        senha = reverse("usuario_senha", kwargs={"usuario_id": self.tecnico.id})
        ativo = reverse("usuario_ativo", kwargs={"usuario_id": self.tecnico.id})
        self.assertEqual(self.client.get(senha).status_code, 404)
        self.assertEqual(self.client.post(ativo).status_code, 404)
