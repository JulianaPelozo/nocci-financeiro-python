# Especificação de Requisitos — Nocci Financeiro

Versão 1.0 · novembro/2026

O Nocci Financeiro é um sistema web de finanças pessoais com três módulos: calculadora de juros, simulador de empréstimo com análise de crédito, e controle de despesas com orçamento mensal. Ele também oferece uma API JSON com as mesmas regras.

## Convenções gerais

- **RG01:** valores monetários usam 2 casas decimais e arredondamento "meio para cima" (0,005 → 0,01).
- **RG02:** campos numéricos aceitam os formatos `1234.56`, `1234,56` e `1.234,56`.
- **RG03:** todo limite informado como "entre X e Y" é **inclusivo**.
- **RG04:** uma entrada inválida não gera resultado. O sistema mostra uma mensagem de erro que indica o campo. Na API, a resposta é **HTTP 400** com `{"erro": "..."}`.

## Requisitos funcionais

### RF01 — Juros simples
Calcula `M = C × (1 + i × n)` e `J = M − C`.
- Capital `C`: entre R$ 0,01 e R$ 1.000.000,00.
- Taxa `i`: entre 0,01% e 100% por período.
- Períodos `n`: inteiro entre 1 e 600.

### RF02 — Juros compostos
Calcula `M = C × (1 + i)^n` e `J = M − C`, com as mesmas faixas de validação do RF01.
- Se o montante passar de R$ 999.999.999.999,99, o sistema recusa o cálculo com mensagem de erro.

### RF03 — Simulação de empréstimo
Gera a tabela de amortização mês a mês (parcela, juros, amortização e saldo devedor), além do total pago e do total de juros.
- Valor: entre R$ 500,00 e R$ 100.000,00.
- Taxa: entre 0,5% e 8% ao mês.
- Prazo: inteiro entre 6 e 120 meses.
- Sistema: `PRICE` (parcelas iguais) ou `SAC` (amortização constante e parcelas decrescentes).
- Os juros do mês incidem sobre o saldo devedor do mês anterior.
- A última parcela é ajustada para que o saldo devedor final seja **exatamente R$ 0,00**.

### RF04 — Análise de crédito
Classifica o pedido de empréstimo a partir da renda mensal, da idade, da situação cadastral (negativado ou não) e do valor da **primeira parcela**.

Comprometimento = parcela ÷ renda × 100.

| Condição | Resultado |
|---|---|
| Idade < 18 ou > 75 | REPROVADO |
| Cliente negativado | REPROVADO |
| Comprometimento > 40% | REPROVADO |
| Comprometimento > 30% e ≤ 40% (sem outro impedimento) | EM ANÁLISE |
| Comprometimento ≤ 30% (sem outro impedimento) | APROVADO |

Quando o pedido é reprovado, o sistema lista **todos** os motivos. Renda e parcela devem ser maiores que zero.

### RF05 — Registro de despesa
- Descrição: entre 3 e 60 caracteres, desconsiderando espaços nas pontas.
- Valor: entre R$ 0,01 e R$ 1.000.000,00.
- Categoria: Alimentação, Moradia, Transporte, Saúde, Lazer, Educação ou Outros.
- Data: formato AAAA-MM-DD, não pode ser futura.
- O usuário pode remover uma despesa já registrada.

### RF06 — Resumo mensal
Para um mês e ano escolhidos, mostra a quantidade de despesas, o total gasto e o valor e o percentual de cada categoria sobre o total, em ordem decrescente de valor.

### RF07 — Alerta de orçamento
O usuário informa o orçamento do mês (maior que zero) e o sistema calcula o percentual usado (gasto ÷ orçamento × 100) e o saldo.

| Percentual usado | Status |
|---|---|
| < 80% | OK |
| ≥ 80% e ≤ 100% | ATENÇÃO |
| > 100% | ESTOURADO |

## Requisitos não funcionais

- **RNF01:** a interface fica em português do Brasil e os valores aparecem no formato `R$ 1.234,56`.
- **RNF02:** a interface pode ser usada em telas a partir de 360 px de largura.
- **RNF03:** a API responde em JSON e os valores monetários vão como texto (ex.: `"1102.50"`).
- **RNF04:** os dados de despesas ficam em memória e são perdidos quando o servidor é reiniciado.

## Endpoints da API

| Método | Rota | Requisito |
|---|---|---|
| POST | `/api/juros` | RF01, RF02 |
| POST | `/api/emprestimo` | RF03 |
| POST | `/api/credito` | RF04 |
| GET / POST | `/api/despesas` | RF05 |
| DELETE | `/api/despesas/<id>` | RF05 |
| GET | `/api/despesas/resumo?ano=&mes=&orcamento=` | RF06, RF07 |
