"""RF04 — Análise de crédito (tabela de decisão)."""

from dataclasses import dataclass, field
from decimal import Decimal

from .validacao import (ErroValidacao, arredondar, para_decimal, para_inteiro)

IDADE_MIN = 18
IDADE_MAX = 75
LIMITE_APROVACAO = Decimal("30")  # % da renda
LIMITE_ANALISE = Decimal("40")  # % da renda

APROVADO = "APROVADO"
EM_ANALISE = "EM ANÁLISE"
REPROVADO = "REPROVADO"


@dataclass
class ResultadoCredito:
    status: str
    comprometimento: Decimal  # % da renda comprometida pela parcela
    motivos: list = field(default_factory=list)

    def como_dict(self) -> dict:
        return {
            "status": self.status,
            "comprometimento": str(self.comprometimento),
            "motivos": self.motivos,
        }


def _para_booleano(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    texto = str(valor).strip().lower()
    if texto in ("true", "1", "sim", "s", "on"):
        return True
    if texto in ("false", "0", "nao", "não", "n", "off", ""):
        return False
    raise ErroValidacao("O campo 'negativado' deve ser verdadeiro ou falso.")


def analisar(renda, idade, negativado, parcela) -> ResultadoCredito:
    renda = para_decimal(renda, "renda")
    idade = para_inteiro(idade, "idade")
    parcela = para_decimal(parcela, "parcela")
    negativado = _para_booleano(negativado)

    if renda <= 0:
        raise ErroValidacao("O campo 'renda' deve ser maior que zero.")
    if parcela <= 0:
        raise ErroValidacao("O campo 'parcela' deve ser maior que zero.")
    if idade < 0 or idade > 130:
        raise ErroValidacao("O campo 'idade' é inválido.")

    # A comparação usa o valor exato; o arredondamento é só para exibição.
    percentual = parcela / renda * 100
    comprometimento = arredondar(percentual)
    motivos = []

    if idade < IDADE_MIN or idade > IDADE_MAX:
        motivos.append(f"Idade fora da faixa permitida ({IDADE_MIN} a {IDADE_MAX} anos).")
    if negativado:
        motivos.append("Cliente com restrição em órgão de proteção ao crédito.")
    if percentual > LIMITE_ANALISE:
        motivos.append(f"Parcela compromete mais de {LIMITE_ANALISE}% da renda.")

    if motivos:
        return ResultadoCredito(REPROVADO, comprometimento, motivos)
    if percentual > LIMITE_APROVACAO:
        return ResultadoCredito(
            EM_ANALISE, comprometimento,
            [f"Parcela compromete entre {LIMITE_APROVACAO}% e {LIMITE_ANALISE}% da renda."],
        )
    return ResultadoCredito(APROVADO, comprometimento, [])
