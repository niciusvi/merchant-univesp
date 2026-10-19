"""Telas do painel inicial e de vencimentos.

Ficam fora de ``views.py`` porque aquele arquivo já passa de 400 linhas e cuida
de cadastro e venda; aqui só existe leitura (consulta de validade).
"""

from datetime import timedelta

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from . import vencimentos


def painel(request: HttpRequest) -> HttpResponse:
    """Tela inicial: números do dia e atalhos para Inventário, Vencimentos e Scanner.

    Exemplo: ``GET /``.
    """
    contexto = {
        "resumo": vencimentos.resumir_vencimentos(hoje=timezone.localdate()),
        "dias_padrao": vencimentos.FILTRO_DIAS_PADRAO,
    }
    return render(request, "painel.html", contexto)


def listar_vencimentos(request: HttpRequest) -> HttpResponse:
    """Lotes que vencem dentro da janela ``?dias=`` (3, 7, 15 ou 30; padrão 7).

    Exemplo: ``GET /vencimentos/?dias=15``.
    """
    try:
        dias = vencimentos.interpretar_filtro_dias(request.GET.get("dias"))
    except ValueError as erro:
        return _responder_filtro_invalido(request, erro)
    hoje = timezone.localdate()
    contexto = {
        "dias": dias,
        "filtros": vencimentos.FILTROS_DIAS_VENCIMENTO,
        "limite": hoje + timedelta(days=dias),
        "lotes": vencimentos.lotes_a_vencer(hoje=hoje, dias=dias),
    }
    return render(request, "vencimentos.html", contexto)


def _responder_filtro_invalido(request: HttpRequest, erro: ValueError) -> HttpResponse:
    # 400 em vez de 500: o problema está no parâmetro enviado, não no servidor.
    contexto = {
        "dias": None,
        "filtros": vencimentos.FILTROS_DIAS_VENCIMENTO,
        "lotes": [],
        "erro": str(erro),
    }
    return render(request, "vencimentos.html", contexto, status=400)
