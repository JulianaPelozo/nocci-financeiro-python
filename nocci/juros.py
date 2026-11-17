"""RF01 e RF02 — Calculadora de juros simples e compostos."""

from dataclasses import dataclass
from decimal import Decimal

from .validacao import (ErroValidacao, arredondar, para_decimal, para_inteiro,
                        validar_faixa)

CAPITAL_MIN = Decimal("0.01")
CAPITAL_MAX = Decimal("1000000.00")
TAXA_MIN = Decimal("0.01")  # % ao período
TAXA_MAX = Decimal("100")  # % ao período
PERIODOS_MIN = 1
PERIODOS_MAX = 600
MONTANTE_MAX = Decimal("999999999999.99")  # R$ 999 bilhões


@dataclass(frozen=True)
class ResultadoJuros:
    tipo: str
    capital: Decimal
    taxa: Decimal
    periodos: int
    juros: Decimal
    montante: Decimal

    def como_dict(self) -> dict:
        return {
            "tipo": self.tipo,
            "capital": str(self.capital),
            "taxa": str(self.taxa),
            "periodos": self.periodos,
            "juros": str(self.juros),
            "montante": str(self.montante),
        }


def _validar(capital, taxa, periodos):
    capital = para_decimal(capital, "capital")
    taxa = para_decimal(taxa, "taxa")
    periodos = para_inteiro(periodos, "periodos")
    validar_faixa(capital, CAPITAL_MIN, CAPITAL_MAX, "capital", "R$")
    validar_faixa(taxa, TAXA_MIN, TAXA_MAX, "taxa", "%")
    validar_faixa(periodos, PERIODOS_MIN, PERIODOS_MAX, "periodos")
    return capital, taxa, periodos


def juros_simples(capital, taxa, periodos) -> ResultadoJuros:
    """M = C * (1 + i * n). A taxa é informada em percentual por período."""
    capital, taxa, periodos = _validar(capital, taxa, periodos)
    i = taxa / 100
    montante = arredondar(capital * (1 + i * periodos))
    return ResultadoJuros("simples", capital, taxa, periodos,
                          montante - arredondar(capital), montante)


def juros_compostos(capital, taxa, periodos) -> ResultadoJuros:
    """M = C * (1 + i) ^ n. A taxa é informada em percentual por período."""
    capital, taxa, periodos = _validar(capital, taxa, periodos)
    i = taxa / 100
    montante = capital * (1 + i) ** periodos
    if montante > MONTANTE_MAX:
        raise ErroValidacao(
            "O montante resultante excede o limite suportado de R$ 999.999.999.999,99."
        )
    montante = arredondar(montante)
    return ResultadoJuros("compostos", capital, taxa, periodos,
                          montante - arredondar(capital), montante)


def calcular(tipo: str, capital, taxa, periodos) -> ResultadoJuros:
    if tipo == "simples":
        return juros_simples(capital, taxa, periodos)
    if tipo == "compostos":
        return juros_compostos(capital, taxa, periodos)
    raise ErroValidacao("O campo 'tipo' deve ser 'simples' ou 'compostos'.")
