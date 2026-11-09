
"""Testes isolados do planejador analítico."""

import json

import pandas as pd

from analytics.planner import planejar_analise


class FakeGerador:
    def __init__(self, resposta):
        self.resposta = resposta

    def gerar(self, mensagens, max_novos_tokens, temperatura):
        return self.resposta


def testar_plano_valido():
    dados = {
        "vendas.csv:vendas": pd.DataFrame({
            "produto": ["A", "B", "A"],
            "valor": [100.0, 200.0, 150.0],
            "data": pd.to_datetime([
                "2026-01-10",
                "2026-01-15",
                "2026-02-10",
            ]),
        })
    }

    resposta = {
        "title": "Relatório de vendas",
        "kpis": [
            {
                "source": "vendas.csv:vendas",
                "label": "Faturamento total",
                "column": "valor",
                "operation": "sum",
                "unit": "R$",
            }
        ],
        "charts": [
            {
                "source": "vendas.csv:vendas",
                "type": "bar",
                "title": "Faturamento por produto",
                "group_column": "produto",
                "value_column": "valor",
                "operation": "sum",
            },
            {
                "source": "vendas.csv:vendas",
                "type": "line",
                "title": "Faturamento mensal",
                "date_column": "data",
                "value_column": "valor",
                "operation": "sum",
            },
        ],
    }

    gerador = FakeGerador(json.dumps(resposta))

    plano = planejar_analise(
        gerador,
        "Gere um relatório de vendas.",
        dados,
    )

    assert plano["titulo"] == "Relatório de vendas"
    assert len(plano["kpis"]) == 1
    assert len(plano["graficos"]) == 2
    assert plano["graficos"][0]["tipo"] == "bar"
    assert plano["graficos"][1]["tipo"] == "line"

    print("Plano válido: OK")


def testar_fonte_inexistente():
    dados = {
        "vendas.csv:vendas": pd.DataFrame({
            "valor": [100, 200],
        })
    }

    resposta = {
        "title": "Relatório",
        "kpis": [
            {
                "source": "arquivo_inexistente",
                "label": "Total",
                "column": "valor",
                "operation": "sum",
                "unit": None,
            }
        ],
        "charts": [],
    }

    gerador = FakeGerador(json.dumps(resposta))

    try:
        planejar_analise(gerador, "Calcule o total.", dados)
    except ValueError as erro:
        assert "Fonte não encontrada" in str(erro)
        print("Rejeição de fonte inexistente: OK")
    else:
        raise AssertionError("Uma fonte inexistente foi aceita.")


def testar_operacao_invalida():
    dados = {
        "vendas.csv:vendas": pd.DataFrame({
            "valor": [100, 200],
        })
    }

    resposta = {
        "title": "Relatório",
        "kpis": [
            {
                "source": "vendas.csv:vendas",
                "label": "Total",
                "column": "valor",
                "operation": "delete",
                "unit": None,
            }
        ],
        "charts": [],
    }

    gerador = FakeGerador(json.dumps(resposta))

    try:
        planejar_analise(gerador, "Calcule o total.", dados)
    except ValueError as erro:
        assert "Operação não permitida" in str(erro)
        print("Rejeição de operação inválida: OK")
    else:
        raise AssertionError("Uma operação inválida foi aceita.")


if __name__ == "__main__":
    testar_plano_valido()
    testar_fonte_inexistente()
    testar_operacao_invalida()

    print("\nTodos os testes passaram!")
