"""Testes dos comandos chamados pelo ``bin/iniciar-container.sh`` a cada subida.

Os dois precisam ser idempotentes: rodar duas vezes tem o mesmo efeito de rodar
uma. Sem isso, cada reinício do contêiner duplicaria produtos ou quebraria por
"usuário já existe".
"""

import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from mercado.models import Product

VARIAVEIS_ADMIN = {
    "DJANGO_SUPERUSER_USERNAME": "dono",
    "DJANGO_SUPERUSER_PASSWORD": "senha-apenas-do-teste-123",
    "DJANGO_SUPERUSER_EMAIL": "dono@exemplo.test",
}
VARIAVEIS_ADMIN_VAZIAS = {nome: "" for nome in VARIAVEIS_ADMIN}


class SemearDadosIniciaisTest(TestCase):
    def test_carrega_o_produto_do_repositorio_original_uma_unica_vez(self) -> None:
        saida = StringIO()

        call_command("semear_dados_iniciais", stdout=saida)
        call_command("semear_dados_iniciais", stdout=saida)

        self.assertEqual(Product.objects.count(), 1)
        produto = Product.objects.get(barcode="123")
        self.assertEqual(produto.name, "teste")
        self.assertEqual(produto.quantity, 88)
        self.assertIn("ignorada", saida.getvalue())

    def test_nao_mexe_em_banco_que_ja_tem_produtos(self) -> None:
        Product.objects.create(name="Outro", barcode="999", price=1)

        call_command("semear_dados_iniciais", stdout=StringIO())

        self.assertFalse(Product.objects.filter(barcode="123").exists())


class CriarAdminInicialTest(TestCase):
    def test_sem_variaveis_nao_cria_ninguem(self) -> None:
        saida = StringIO()
        with patch.dict(os.environ, VARIAVEIS_ADMIN_VAZIAS):
            call_command("criar_admin_inicial", stdout=saida)

        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertIn("não criado", saida.getvalue())

    def test_cria_superusuario_e_nao_duplica_nem_mostra_a_senha(self) -> None:
        saida = StringIO()
        with patch.dict(os.environ, VARIAVEIS_ADMIN):
            call_command("criar_admin_inicial", stdout=saida)
            call_command("criar_admin_inicial", stdout=saida)

        usuarios = get_user_model().objects.all()
        self.assertEqual(usuarios.count(), 1)
        self.assertTrue(usuarios[0].is_superuser)
        self.assertTrue(
            usuarios[0].check_password(VARIAVEIS_ADMIN["DJANGO_SUPERUSER_PASSWORD"])
        )
        self.assertIn("já existe", saida.getvalue())
        self.assertNotIn(VARIAVEIS_ADMIN["DJANGO_SUPERUSER_PASSWORD"], saida.getvalue())
