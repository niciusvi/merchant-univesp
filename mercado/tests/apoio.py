"""Apoio aos testes de tela: usuário logado sem repetir código em cada classe.

Não começa com ``test`` de propósito: o Django não o executa como teste.
"""

from django.contrib.auth.models import User
from django.test import Client

SENHA_DE_TESTE = "senha-forte-de-teste-123"


def criar_usuario(nome: str = "funcionario", administrador: bool = False) -> User:
    """Cria usuário comum ou administrador com ``SENHA_DE_TESTE``.

    Exemplo: ``criar_usuario("joana")``; ``criar_usuario("dono", administrador=True)``.
    """
    if administrador:
        return User.objects.create_superuser(nome, "", SENHA_DE_TESTE)
    return User.objects.create_user(nome, "", SENHA_DE_TESTE)


def entrar_como_usuario(client: Client, administrador: bool = False) -> User:
    """Cria um usuário (ou administrador) e já o loga no ``client`` de teste.

    Exemplo, no ``setUp``: ``self.usuario = entrar_como_usuario(self.client)``.
    """
    nome = "admin_teste" if administrador else "funcionario"
    usuario = criar_usuario(nome, administrador)
    client.force_login(usuario)
    return usuario
