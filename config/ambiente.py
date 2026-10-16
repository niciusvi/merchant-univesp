"""Leitura tipada das variáveis de ambiente usadas pelo ``settings.py``.

Toda configuração que muda entre a máquina local, o Cloud Run e a stack do
Portainer entra por aqui. Não há valores reais neste arquivo: os padrões
servem só ao desenvolvimento local e o ``.env.example`` documenta cada um.

Exemplo::

    from config import ambiente

    DEBUG = ambiente.ler_booleano("DJANGO_DEBUG", padrao=False)
    SECRET_KEY = ambiente.ler_texto("DJANGO_SECRET_KEY")
"""

from __future__ import annotations

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

VALORES_VERDADEIROS: tuple[str, ...] = ("1", "true", "sim", "yes", "on")
VALORES_FALSOS: tuple[str, ...] = ("0", "false", "nao", "não", "no", "off")

# Abaixo disso um segredo é fácil de adivinhar por força bruta.
TAMANHO_MINIMO_SEGREDO: int = 32


def carregar_arquivo_env(caminho: Path) -> bool:
    """Completa ``os.environ`` com um arquivo ``.env``, sem sobrescrever o que já existe.

    Devolve ``False`` quando o arquivo não existe (normal dentro do contêiner,
    onde as variáveis vêm do Portainer). Exemplo: ``carregar_arquivo_env(BASE_DIR / ".env")``.
    """
    if not caminho.is_file():
        return False
    load_dotenv(caminho, override=False)
    return True


def ler_texto(nome: str, padrao: str | None = None) -> str:
    """Lê uma variável de texto; sem ``padrao`` ela é obrigatória.

    Exemplo: ``ler_texto("DJANGO_SECRET_KEY")`` ou ``ler_texto("DJANGO_DB_PATH", padrao="db.sqlite3")``.
    """
    valor = os.environ.get(nome, "").strip()
    if valor:
        return valor
    if padrao is not None:
        return padrao
    raise ImproperlyConfigured(
        f"Variável de ambiente {nome} não definida (recebido: vazio). "
        "Esperado: texto não vazio. Copie .env.example para .env e preencha."
    )


def ler_booleano(nome: str, padrao: bool) -> bool:
    """Lê ``1/0``, ``true/false``, ``sim/nao``; vazio usa ``padrao``.

    Exemplo: ``ler_booleano("DJANGO_DEBUG", padrao=False)``.
    """
    bruto = os.environ.get(nome, "").strip().lower()
    if bruto == "":
        return padrao
    if bruto in VALORES_VERDADEIROS:
        return True
    if bruto in VALORES_FALSOS:
        return False
    raise ImproperlyConfigured(
        f"Variável de ambiente {nome} com valor inválido: {bruto!r}. "
        f"Esperado um de {VALORES_VERDADEIROS + VALORES_FALSOS}."
    )


def ler_lista(nome: str, padrao: tuple[str, ...] = ()) -> list[str]:
    """Lê uma lista separada por vírgulas, ignorando espaços e itens vazios.

    Exemplo: ``DJANGO_ALLOWED_HOSTS=meusite.com, localhost`` vira
    ``["meusite.com", "localhost"]``; vazio devolve ``list(padrao)``.
    """
    bruto = os.environ.get(nome, "")
    itens = [item.strip() for item in bruto.split(",") if item.strip()]
    return itens or list(padrao)


def exigir_segredo_forte(nome: str, valor: str, depuracao: bool) -> str:
    """Em produção (``depuracao=False``) recusa o valor de exemplo e segredos curtos.

    A mensagem nunca mostra o valor recebido: segredo não vai para log.
    Exemplo: ``exigir_segredo_forte("DJANGO_SECRET_KEY", chave, DEBUG)``.
    """
    if depuracao:
        return valor
    if "TROQUE" in valor.upper() or len(valor) < TAMANHO_MINIMO_SEGREDO:
        raise ImproperlyConfigured(
            f"{nome} fraca para produção (recebido: texto com {len(valor)} "
            f"caracteres, conteúdo omitido). Esperado: ao menos {TAMANHO_MINIMO_SEGREDO} "
            "caracteres aleatórios, sem o valor de exemplo. Gere com: "
            'python -c "import secrets; print(secrets.token_urlsafe(50))"'
        )
    return valor
