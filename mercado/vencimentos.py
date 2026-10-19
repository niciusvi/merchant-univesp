"""Regras de vencimento dos lotes.

Módulo sem view nem template: recebe a data de "hoje" por parâmetro para que
os testes controlem o calendário (injeção de dependência) e para que a mesma
conta sirva ao painel, à tela de vencimentos e, no futuro, à API.

Exemplo de uso::

    from django.utils import timezone
    linhas = lotes_a_vencer(hoje=timezone.localdate(), dias=7)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from django.db.models import QuerySet

from .models import Product, ProductBatch

# Janelas oferecidas como filtro na tela de vencimentos, em dias.
FILTROS_DIAS_VENCIMENTO: tuple[int, ...] = (3, 7, 15, 30)
FILTRO_DIAS_PADRAO: int = 7


def interpretar_filtro_dias(valor_bruto: str | None) -> int:
    """Converte o parâmetro ``?dias=`` da URL em uma janela válida.

    Exemplo: ``interpretar_filtro_dias("15")`` devolve ``15``;
    ``None`` ou ``""`` devolvem ``FILTRO_DIAS_PADRAO``.
    Levanta ``ValueError`` para qualquer valor fora de ``FILTROS_DIAS_VENCIMENTO``.
    """
    if not valor_bruto:
        return FILTRO_DIAS_PADRAO
    # isdigit() recusa sinal, espaço e letras: "-3" e "abc" não viram int.
    if not valor_bruto.isdigit():
        raise _erro_filtro_invalido(valor_bruto)
    dias = int(valor_bruto)
    if dias not in FILTROS_DIAS_VENCIMENTO:
        raise _erro_filtro_invalido(valor_bruto)
    return dias


def _erro_filtro_invalido(valor_bruto: str) -> ValueError:
    return ValueError(
        f"Filtro de dias inválido: {valor_bruto!r}. "
        f"Esperado um número inteiro entre {FILTROS_DIAS_VENCIMENTO}."
    )


def dias_restantes(hoje: date, validade: date) -> int:
    """Dias entre hoje e a validade; negativo quando já venceu.

    Exemplo: ``dias_restantes(date(2026, 10, 16), date(2026, 10, 18))`` devolve ``2``.
    """
    return (validade - hoje).days


def descrever_situacao(dias: int) -> str:
    """Texto curto da urgência para a tela.

    Exemplo: ``descrever_situacao(-1)`` devolve ``"Vencido"``;
    ``descrever_situacao(5)`` devolve ``"Vence em 5 dias"``.
    """
    if dias < 0:
        return "Vencido"
    if dias == 0:
        return "Vence hoje"
    if dias == 1:
        return "Vence amanhã"
    return f"Vence em {dias} dias"


@dataclass(frozen=True)
class LoteVencendo:
    """Uma linha pronta para a tela de vencimentos (nenhuma conta no template)."""

    produto: str
    marca: str
    codigo_barras: str
    numero_lote: str
    validade: date
    quantidade: int
    dias_restantes: int
    situacao: str
    vencido: bool


def lotes_a_vencer(hoje: date, dias: int) -> list[LoteVencendo]:
    """Lotes com estoque cuja validade cai até ``hoje + dias``, do mais urgente ao menos.

    Inclui lotes já vencidos: são o caso mais urgente para tirar da gôndola.
    Lotes zerados ou sem validade ficam de fora.
    Exemplo: ``lotes_a_vencer(date(2026, 10, 16), 7)``.
    """
    limite = hoje + timedelta(days=dias)
    lotes = _lotes_com_estoque_e_validade().filter(expiration_date__lte=limite)
    return [_montar_linha(hoje, lote) for lote in lotes]


def _lotes_com_estoque_e_validade() -> QuerySet[ProductBatch]:
    return (
        ProductBatch.objects.select_related("product")
        .filter(quantity__gt=0, expiration_date__isnull=False)
        .order_by("expiration_date", "product__name", "id")
    )


def _montar_linha(hoje: date, lote: ProductBatch) -> LoteVencendo:
    # O filtro acima garante validade preenchida; o assert documenta isso ao leitor.
    assert lote.expiration_date is not None
    dias = dias_restantes(hoje, lote.expiration_date)
    return LoteVencendo(
        produto=lote.product.name,
        marca=lote.product.brand,
        codigo_barras=lote.product.barcode,
        numero_lote=lote.batch_number,
        validade=lote.expiration_date,
        quantidade=lote.quantity,
        dias_restantes=dias,
        situacao=descrever_situacao(dias),
        vencido=dias < 0,
    )


@dataclass(frozen=True)
class ResumoVencimentos:
    """Números mostrados no painel inicial."""

    total_produtos: int
    lotes_vencidos: int
    # Vencem de hoje até FILTRO_DIAS_PADRAO dias, sem contar os já vencidos.
    lotes_proximos: int


def resumir_vencimentos(hoje: date) -> ResumoVencimentos:
    """Conta produtos cadastrados, lotes vencidos e lotes que vencem em breve.

    Exemplo: ``resumir_vencimentos(date(2026, 10, 16)).lotes_vencidos``.
    """
    lotes = _lotes_com_estoque_e_validade()
    limite = hoje + timedelta(days=FILTRO_DIAS_PADRAO)
    return ResumoVencimentos(
        total_produtos=Product.objects.count(),
        lotes_vencidos=lotes.filter(expiration_date__lt=hoje).count(),
        lotes_proximos=lotes.filter(expiration_date__range=(hoje, limite)).count(),
    )
