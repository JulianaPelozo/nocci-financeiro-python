"""RF05, RF06 e RF07 — Controle de despesas, resumo mensal e alerta de orçamento."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from itertools import count

from .validacao import ErroValidacao, arredondar, para_decimal, validar_faixa

CATEGORIAS = ("Alimentação", "Moradia", "Transporte", "Saúde",
              "Lazer", "Educação", "Outros")
DESCRICAO_MIN = 3
DESCRICAO_MAX = 60
VALOR_MIN = Decimal("0.01")
VALOR_MAX = Decimal("1000000.00")
ALERTA_ATENCAO = Decimal("80")  # % do orçamento
ALERTA_ESTOURO = Decimal("100")  # % do orçamento

STATUS_OK = "OK"
STATUS_ATENCAO = "ATENÇÃO"
STATUS_ESTOURADO = "ESTOURADO"


@dataclass(frozen=True)
class Despesa:
    id: int
    descricao: str
    valor: Decimal
    categoria: str
    data: date

    def como_dict(self) -> dict:
        return {
            "id": self.id,
            "descricao": self.descricao,
            "valor": str(self.valor),
            "categoria": self.categoria,
            "data": self.data.isoformat(),
        }


def _para_data(valor) -> date:
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(str(valor).strip())
    except ValueError:
        raise ErroValidacao("O campo 'data' deve estar no formato AAAA-MM-DD.") from None


class ControleDespesas:
    """Armazena despesas em memória (os dados são perdidos ao reiniciar)."""

    def __init__(self):
        self._despesas: dict[int, Despesa] = {}
        self._ids = count(1)

    # RF05 -------------------------------------------------------------
    def registrar(self, descricao, valor, categoria, data, hoje=None) -> Despesa:
        hoje = hoje or date.today()
        descricao = str(descricao or "").strip()
        if not DESCRICAO_MIN <= len(descricao) <= DESCRICAO_MAX:
            raise ErroValidacao(
                f"O campo 'descricao' deve ter entre {DESCRICAO_MIN} e "
                f"{DESCRICAO_MAX} caracteres."
            )
        valor = para_decimal(valor, "valor")
        validar_faixa(valor, VALOR_MIN, VALOR_MAX, "valor", "R$")
        if categoria not in CATEGORIAS:
            raise ErroValidacao(
                "O campo 'categoria' deve ser um de: " + ", ".join(CATEGORIAS) + "."
            )
        data = _para_data(data)
        if data > hoje:
            raise ErroValidacao("O campo 'data' não pode estar no futuro.")

        despesa = Despesa(next(self._ids), descricao, arredondar(valor), categoria, data)
        self._despesas[despesa.id] = despesa
        return despesa

    def remover(self, despesa_id: int) -> None:
        if despesa_id not in self._despesas:
            raise KeyError(despesa_id)
        del self._despesas[despesa_id]

    def listar(self, ano: int | None = None, mes: int | None = None) -> list[Despesa]:
        itens = sorted(self._despesas.values(), key=lambda d: (d.data, d.id))
        if ano is not None:
            itens = [d for d in itens if d.data.year == ano]
        if mes is not None:
            itens = [d for d in itens if d.data.month == mes]
        return itens

    # RF06 -------------------------------------------------------------
    def resumo_mensal(self, ano: int, mes: int) -> dict:
        despesas = self.listar(ano, mes)
        total = sum((d.valor for d in despesas), Decimal("0"))
        por_categoria = {}
        for d in despesas:
            por_categoria[d.categoria] = por_categoria.get(d.categoria, Decimal("0")) + d.valor
        return {
            "ano": ano,
            "mes": mes,
            "quantidade": len(despesas),
            "total": total,
            "por_categoria": {
                cat: {
                    "valor": valor,
                    "percentual": arredondar(valor / total * 100) if total else Decimal("0"),
                }
                for cat, valor in sorted(por_categoria.items(), key=lambda x: -x[1])
            },
        }

    # RF07 -------------------------------------------------------------
    def status_orcamento(self, ano: int, mes: int, orcamento) -> dict:
        orcamento = para_decimal(orcamento, "orcamento")
        if orcamento <= 0:
            raise ErroValidacao("O campo 'orcamento' deve ser maior que zero.")
        total = self.resumo_mensal(ano, mes)["total"]
        # A comparação usa o valor exato; o arredondamento é só para exibição.
        exato = total / orcamento * 100
        percentual = arredondar(exato)
        if exato > ALERTA_ESTOURO:
            status = STATUS_ESTOURADO
        elif exato >= ALERTA_ATENCAO:
            status = STATUS_ATENCAO
        else:
            status = STATUS_OK
        return {
            "orcamento": arredondar(orcamento),
            "gasto": total,
            "percentual": percentual,
            "saldo": arredondar(orcamento - total),
            "status": status,
        }
