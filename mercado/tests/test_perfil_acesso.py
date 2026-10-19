"""Separação entre usuários do mercado e a conta técnica do Django.

- Conta técnica (superuser) entra em ``/admin/``, mas não no painel.
- Usuário do mercado entra no painel, mas não em ``/admin/``.
- O administrador do mercado nasce de ``MERCADO_ADMIN_*``, nunca de ``DJANGO_SUPERUSER_*``.
"""

import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from mercado.models import PerfilDeAcesso
from mercado.tests.apoio import (
    SENHA_DE_TESTE,
    criar_superusuario_django,
    entrar_como_usuario,
)

VARIAVEIS_MERCADO = {
    "MERCADO_ADMIN_USUARIO": "dona",
    "MERCADO_ADMIN_SENHA": "senha-da-dona-apenas-teste-123",
}


class ContaTecnicaDoDjangoTest(TestCase):
    def setUp(self) -> None:
        self.tecnico = criar_superusuario_django()
        self.client.force_login(self.tecnico)

    def test_nao_abre_o_painel_e_ve_a_tela_de_sem_acesso(self) -> None:
        resposta = self.client.get(reverse("painel"))
        self.assertEqual(resposta.status_code, 403)
        self.assertTemplateUsed(resposta, "sem_acesso.html")
        self.assertEqual(self.client.get(reverse("estoque")).status_code, 403)
        self.assertEqual(self.client.get(reverse("usuarios")).status_code, 403)

    def test_continua_entrando_no_admin_do_django(self) -> None:
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_consegue_sair_mesmo_sem_perfil(self) -> None:
        self.assertRedirects(self.client.post(reverse("sair")), reverse("entrar"))


class UsuarioDoMercadoTest(TestCase):
    def test_nao_e_staff_e_o_admin_do_django_o_recusa(self) -> None:
        usuario = entrar_como_usuario(self.client, administrador=True)
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        resposta = self.client.get("/admin/")
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta["Location"].startswith("/admin/login/"))

    def test_administrador_do_mercado_nao_depende_de_superuser(self) -> None:
        entrar_como_usuario(self.client, administrador=True)
        self.assertEqual(self.client.get(reverse("usuarios")).status_code, 200)


class CriarAdministradorDoMercadoTest(TestCase):
    def test_sem_variaveis_nao_cria(self) -> None:
        with patch.dict(
            os.environ, {"MERCADO_ADMIN_USUARIO": "", "MERCADO_ADMIN_SENHA": ""}
        ):
            call_command("criar_administrador_do_mercado", stdout=StringIO())
        self.assertEqual(User.objects.count(), 0)

    def test_cria_administrador_do_mercado_sem_poderes_do_django(self) -> None:
        saida = StringIO()
        with patch.dict(os.environ, VARIAVEIS_MERCADO):
            call_command("criar_administrador_do_mercado", stdout=saida)
            call_command("criar_administrador_do_mercado", stdout=saida)

        dona = User.objects.get(username="dona")
        self.assertTrue(dona.check_password(VARIAVEIS_MERCADO["MERCADO_ADMIN_SENHA"]))
        self.assertFalse(dona.is_staff)
        self.assertFalse(dona.is_superuser)
        self.assertTrue(PerfilDeAcesso.objects.get(usuario=dona).administrador)
        self.assertEqual(User.objects.count(), 1)
        self.assertIn("já existe", saida.getvalue())
        self.assertNotIn(VARIAVEIS_MERCADO["MERCADO_ADMIN_SENHA"], saida.getvalue())

    def test_conta_tecnica_e_administrador_do_mercado_sao_contas_diferentes(
        self,
    ) -> None:
        criar_superusuario_django("tecnico")
        with patch.dict(os.environ, VARIAVEIS_MERCADO):
            call_command("criar_administrador_do_mercado", stdout=StringIO())
        self.assertEqual(User.objects.count(), 2)
        self.assertFalse(
            PerfilDeAcesso.objects.filter(usuario__username="tecnico").exists()
        )
        self.client.login(
            username="dona", password=VARIAVEIS_MERCADO["MERCADO_ADMIN_SENHA"]
        )
        self.assertEqual(self.client.get(reverse("painel")).status_code, 200)
        self.client.logout()
        self.client.login(username="tecnico", password=SENHA_DE_TESTE)
        self.assertEqual(self.client.get(reverse("painel")).status_code, 403)
