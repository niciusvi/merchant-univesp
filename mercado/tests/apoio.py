"""Apoio aos testes de tela: usuários do mercado prontos, sem repetir código.

Não começa com ``test`` de propósito: o Django não o executa como teste.
"""

from django.contrib.auth.models import User
from django.test import Client

from mercado.models import PerfilDeAcesso

SENHA_DE_TESTE = "senha-forte-de-teste-123"


def criar_usuario(nome: str = "funcionario", administrador: bool = False) -> User:
    """Cria usuário do mercado (com perfil) comum ou administrador.

    Nunca é staff nem superuser: essas flags são da conta técnica do Django.
    Exemplo: ``criar_usuario("joana")``; ``criar_usuario("dono", administrador=True)``.
    """
    usuario = User.objects.create_user(nome, "", SENHA_DE_TESTE)
    PerfilDeAcesso.objects.create(usuario=usuario, administrador=administrador)
    return usuario


def criar_superusuario_django(nome: str = "tecnico") -> User:
    """Conta técnica do Django (``/admin/``), sem perfil do mercado."""
    return User.objects.create_superuser(nome, "", SENHA_DE_TESTE)


def entrar_como_usuario(client: Client, administrador: bool = False) -> User:
    """Cria um usuário do mercado (ou administrador) e já o loga no ``client``.

    Exemplo, no ``setUp``: ``self.usuario = entrar_como_usuario(self.client)``.
    """
    nome = "admin_teste" if administrador else "funcionario"
    usuario = criar_usuario(nome, administrador)
    client.force_login(usuario)
    return usuario
