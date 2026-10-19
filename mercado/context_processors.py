"""Variáveis de template ligadas ao papel do usuário no mercado.

Registrado em ``TEMPLATES[...]['OPTIONS']['context_processors']``. Assim o
``base.html`` decide se mostra o link "Usuários" sem consultar
``is_superuser`` (que agora é só do Django) nem repetir a regra em cada view.
"""

from django.http import HttpRequest

from .autorizacao import eh_administrador


def papel_do_mercado(request: HttpRequest) -> dict[str, bool]:
    """Expõe ``administrador_do_mercado`` a todos os templates.

    Exemplo no template: ``{% if administrador_do_mercado %}...{% endif %}``.
    """
    return {"administrador_do_mercado": eh_administrador(request.user)}
