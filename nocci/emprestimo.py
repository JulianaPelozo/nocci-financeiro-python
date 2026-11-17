"""RF03 — Simulação de empréstimo pelos sistemas PRICE e SAC."""

from dataclasses import dataclass, field
from decimal import Decimal

from .validacao import (ErroValidacao, arredondar, para_decimal, para_inteiro,
                        validar_faixa)

VALOR_MIN = Decimal("500.00")
VALOR_MAX = Decimal("100000.00")
PRAZO_MIN = 6
PRAZO_MAX = 120
TAXA_MIN = Decimal("0.5")  # % ao mês
TAXA_MAX = Decimal("8")  # % ao mês
SISTEMAS = ("PRICE", "SAC")


@dataclass(frozen=True)
class Parcela:
    numero: int
    valor: Decimal
    juros: Decimal
    amortizacao: Decimal
    saldo: Decimal

    def como_dict(self) -> dict:
        return {
            "numero": self.numero,
            "valor": str(self.valor),
            "juros": str(self.juros),
            "amortizacao": str(self.amortizacao),
            "saldo": str(self.saldo),
        }


@dataclass
class Simulacao:
    sistema: str
    valor: Decimal
    taxa: Decimal
    prazo: int
    parcelas: list = field(default_factory=list)

    @property
    def primeira_parcela(self) -> Decimal:
        return self.parcelas[0].valor

    @property
    def total_pago(self) -> Decimal:
        return sum((p.valor for p in self.parcelas), Decimal("0"))

    @property
    def total_juros(self) -> Decimal:
        return sum((p.juros for p in self.parcelas), Decimal("0"))

    def como_dict(self) -> dict:
        return {
            "sistema": self.sistema,
            "valor": str(self.valor),
            "taxa": str(self.taxa),
            "prazo": self.prazo,
            "primeira_parcela": str(self.primeira_parcela),
            "total_pago": str(self.total_pago),
            "total_juros": str(self.total_juros),
            "parcelas": [p.como_dict() for p in self.parcelas],
        }


def simular(valor, taxa, prazo, sistema="PRICE") -> Simulacao:
    valor = para_decimal(valor, "valor")
    taxa = para_decimal(taxa, "taxa")
    prazo = para_inteiro(prazo, "prazo")
    sistema = str(sistema or "").strip().upper()

    validar_faixa(valor, VALOR_MIN, VALOR_MAX, "valor", "R$")
    validar_faixa(taxa, TAXA_MIN, TAXA_MAX, "taxa", "% a.m.")
    validar_faixa(prazo, PRAZO_MIN, PRAZO_MAX, "prazo", "meses")
    if sistema not in SISTEMAS:
        raise ErroValidacao("O campo 'sistema' deve ser 'PRICE' ou 'SAC'.")

    i = taxa / 100
    sim = Simulacao(sistema, arredondar(valor), taxa, prazo)
    saldo = sim.valor

    if sistema == "PRICE":
        prestacao = arredondar(valor * i / (1 - (1 + i) ** -prazo))
    else:
        amortizacao_fixa = arredondar(valor / prazo)

    for n in range(1, prazo + 1):
        juros = arredondar(saldo * i)
        if n == prazo:
            # Última parcela quita exatamente o saldo devedor restante.
            amortizacao = saldo
        elif sistema == "PRICE":
            amortizacao = prestacao - juros
        else:
            amortizacao = amortizacao_fixa
        saldo = saldo - amortizacao
        sim.parcelas.append(
            Parcela(n, amortizacao + juros, juros, amortizacao, saldo)
        )

    return sim
