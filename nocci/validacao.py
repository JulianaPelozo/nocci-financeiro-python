"""Funções utilitárias de validação e conversão de valores."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENTAVOS = Decimal("0.01")


class ErroValidacao(ValueError):
    """Erro lançado quando um dado de entrada viola uma regra de negócio."""


def arredondar(valor: Decimal) -> Decimal:
    """Arredonda para 2 casas decimais (meio para cima), padrão monetário."""
    return Decimal(valor).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def para_decimal(valor, campo: str) -> Decimal:
    """Converte texto ou número em Decimal.

    Aceita os formatos "1234.56", "1234,56" e "1.234,56".
    """
    if valor is None or (isinstance(valor, str) and valor.strip() == ""):
        raise ErroValidacao(f"O campo '{campo}' é obrigatório.")
    if isinstance(valor, bool):
        raise ErroValidacao(f"O campo '{campo}' deve ser numérico.")
    if isinstance(valor, (int, Decimal)):
        numero = Decimal(valor)
    elif isinstance(valor, float):
        numero = Decimal(str(valor))
    else:
        texto = str(valor).strip().replace("R$", "").replace(" ", "")
        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
        try:
            numero = Decimal(texto)
        except InvalidOperation:
            raise ErroValidacao(f"O campo '{campo}' deve ser numérico.") from None
    if not numero.is_finite():
        raise ErroValidacao(f"O campo '{campo}' deve ser numérico.")
    return numero


def para_inteiro(valor, campo: str) -> int:
    """Converte texto ou número em inteiro, rejeitando valores fracionários."""
    numero = para_decimal(valor, campo)
    if numero != numero.to_integral_value():
        raise ErroValidacao(f"O campo '{campo}' deve ser um número inteiro.")
    return int(numero)


def formatar_numero(valor, casas: int | None = None) -> str:
    """Formata no padrão brasileiro: 1234567.8 -> '1.234.567,8'."""
    numero = Decimal(valor)
    if casas is None:
        texto = f"{numero:,f}"
    else:
        texto = f"{numero:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_moeda(valor) -> str:
    return f"R$ {formatar_numero(valor, 2)}"


def validar_faixa(valor, minimo, maximo, campo: str, unidade: str = ""):
    """Garante que minimo <= valor <= maximo (limites inclusivos)."""
    if valor < minimo or valor > maximo:
        if unidade == "R$":
            de, ate = formatar_moeda(minimo), formatar_moeda(maximo)
        else:
            if not unidade:
                sufixo = ""
            elif unidade.startswith("%"):
                sufixo = unidade
            else:
                sufixo = f" {unidade}"
            de = formatar_numero(minimo) + sufixo
            ate = formatar_numero(maximo) + sufixo
        final = "" if ate.endswith(".") else "."
        raise ErroValidacao(f"O campo '{campo}' deve estar entre {de} e {ate}{final}")
    return valor
