"""Aplicação web e API JSON do Nocci Financeiro."""

from datetime import date

from flask import Flask, jsonify, redirect, render_template, request, url_for

from . import credito, emprestimo, juros
from .despesas import CATEGORIAS, ControleDespesas
from .validacao import ErroValidacao, formatar_moeda, para_inteiro


def _ano_mes(origem) -> tuple[int, int]:
    hoje = date.today()
    ano = para_inteiro(origem.get("ano") or hoje.year, "ano")
    mes = para_inteiro(origem.get("mes") or hoje.month, "mes")
    if not 1 <= mes <= 12:
        raise ErroValidacao("O campo 'mes' deve estar entre 1 e 12.")
    return ano, mes


def create_app() -> Flask:
    app = Flask(__name__)
    app.json.sort_keys = False
    controle = ControleDespesas()
    app.extensions["controle_despesas"] = controle

    @app.template_filter("moeda")
    def moeda(valor):
        return formatar_moeda(valor)

    # ------------------------------------------------------------------ páginas
    @app.get("/")
    def inicio():
        return render_template("inicio.html")

    @app.route("/juros", methods=["GET", "POST"])
    def pagina_juros():
        resultado, erro = None, None
        dados = request.form if request.method == "POST" else {}
        if request.method == "POST":
            try:
                resultado = juros.calcular(dados.get("tipo"), dados.get("capital"),
                                           dados.get("taxa"), dados.get("periodos"))
            except ErroValidacao as e:
                erro = str(e)
        return render_template("juros.html", resultado=resultado, erro=erro, dados=dados)

    @app.route("/emprestimo", methods=["GET", "POST"])
    def pagina_emprestimo():
        simulacao, analise, erro = None, None, None
        dados = request.form if request.method == "POST" else {}
        if request.method == "POST":
            try:
                simulacao = emprestimo.simular(dados.get("valor"), dados.get("taxa"),
                                               dados.get("prazo"), dados.get("sistema"))
                if dados.get("renda"):
                    analise = credito.analisar(dados.get("renda"), dados.get("idade"),
                                               dados.get("negativado", "nao"),
                                               simulacao.primeira_parcela)
            except ErroValidacao as e:
                erro = str(e)
        return render_template("emprestimo.html", simulacao=simulacao, analise=analise,
                               erro=erro, dados=dados)

    @app.route("/despesas", methods=["GET", "POST"])
    def pagina_despesas():
        erro, sucesso = None, None
        dados = request.form if request.method == "POST" else {}
        if request.method == "POST":
            try:
                d = controle.registrar(dados.get("descricao"), dados.get("valor"),
                                       dados.get("categoria"), dados.get("data"))
                sucesso = f"Despesa “{d.descricao}” registrada."
                dados = {}
            except ErroValidacao as e:
                erro = str(e)

        orcamento_status = None
        try:
            ano, mes = _ano_mes(request.args)
            resumo = controle.resumo_mensal(ano, mes)
            if request.args.get("orcamento"):
                orcamento_status = controle.status_orcamento(ano, mes, request.args["orcamento"])
        except ErroValidacao as e:
            erro = erro or str(e)
            hoje = date.today()
            ano, mes = hoje.year, hoje.month
            resumo = controle.resumo_mensal(ano, mes)

        return render_template(
            "despesas.html", categorias=CATEGORIAS, despesas=controle.listar(ano, mes),
            resumo=resumo, orcamento=orcamento_status, erro=erro, sucesso=sucesso,
            dados=dados, ano=ano, mes=mes, hoje=date.today().isoformat(),
            orcamento_informado=request.args.get("orcamento", ""),
        )

    @app.post("/despesas/<int:despesa_id>/remover")
    def remover_despesa(despesa_id):
        try:
            controle.remover(despesa_id)
        except KeyError:
            pass
        return redirect(url_for("pagina_despesas", **request.args))

    # ----------------------------------------------------------------------- API
    @app.errorhandler(ErroValidacao)
    def erro_validacao(e):
        if request.path.startswith("/api/"):
            return jsonify({"erro": str(e)}), 400
        raise e

    def corpo_json() -> dict:
        corpo = request.get_json(silent=True)
        if not isinstance(corpo, dict):
            raise ErroValidacao("O corpo da requisição deve ser um objeto JSON.")
        return corpo

    @app.post("/api/juros")
    def api_juros():
        c = corpo_json()
        r = juros.calcular(c.get("tipo"), c.get("capital"), c.get("taxa"), c.get("periodos"))
        return jsonify(r.como_dict())

    @app.post("/api/emprestimo")
    def api_emprestimo():
        c = corpo_json()
        s = emprestimo.simular(c.get("valor"), c.get("taxa"), c.get("prazo"),
                               c.get("sistema", "PRICE"))
        return jsonify(s.como_dict())

    @app.post("/api/credito")
    def api_credito():
        c = corpo_json()
        r = credito.analisar(c.get("renda"), c.get("idade"),
                             c.get("negativado", False), c.get("parcela"))
        return jsonify(r.como_dict())

    @app.get("/api/despesas")
    def api_listar_despesas():
        ano = request.args.get("ano")
        mes = request.args.get("mes")
        itens = controle.listar(para_inteiro(ano, "ano") if ano else None,
                                para_inteiro(mes, "mes") if mes else None)
        return jsonify([d.como_dict() for d in itens])

    @app.post("/api/despesas")
    def api_criar_despesa():
        c = corpo_json()
        d = controle.registrar(c.get("descricao"), c.get("valor"),
                               c.get("categoria"), c.get("data"))
        return jsonify(d.como_dict()), 201

    @app.delete("/api/despesas/<int:despesa_id>")
    def api_remover_despesa(despesa_id):
        try:
            controle.remover(despesa_id)
        except KeyError:
            return jsonify({"erro": "Despesa não encontrada."}), 404
        return "", 204

    @app.get("/api/despesas/resumo")
    def api_resumo():
        ano, mes = _ano_mes(request.args)
        r = controle.resumo_mensal(ano, mes)
        resposta = {
            "ano": r["ano"], "mes": r["mes"], "quantidade": r["quantidade"],
            "total": str(r["total"]),
            "por_categoria": {k: {"valor": str(v["valor"]), "percentual": str(v["percentual"])}
                              for k, v in r["por_categoria"].items()},
        }
        if request.args.get("orcamento"):
            o = controle.status_orcamento(ano, mes, request.args["orcamento"])
            resposta["orcamento"] = {k: str(v) for k, v in o.items()}
        return jsonify(resposta)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
