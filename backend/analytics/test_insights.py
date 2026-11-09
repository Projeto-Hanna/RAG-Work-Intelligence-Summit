
"""Testes isolados da geração de insights."""

import json

from analytics.insights import interpretar_resultados


class FakeGerador:
    def __init__(self, resposta):
        self.resposta = resposta

    def gerar(self, mensagens, max_novos_tokens, temperatura):
        return self.resposta


def criar_relatorio():
    return {
        "title": "Relatório de vendas",
        "kpis": [
            {
                "label": "Faturamento total",
                "value": 450.0,
                "unit": "R$",
            }
        ],
        "charts": [
            {
                "type": "bar",
                "title": "Vendas por produto",
                "labels": ["A", "B"],
                "values": [250.0, 200.0],
            }
        ],
        "sources": ["vendas.csv:vendas"],
    }


def testar_insights_validos():
    resposta = {
        "summary": "O faturamento total foi de R$ 450,00.",
        "insights": [
            {
                "title": "Produto A em destaque",
                "description": "O produto A representa o maior faturamento.",
                "type": "positive",
            }
        ],
    }

    gerador = FakeGerador(json.dumps(resposta))

    resultado = interpretar_resultados(
        gerador,
        criar_relatorio(),
    )

    assert resultado["summary"] == resposta["summary"]
    assert len(resultado["insights"]) == 1
    assert resultado["insights"][0]["type"] == "positive"

    print("Geração de insights: OK")


def testar_json_invalido():
    gerador = FakeGerador("resposta sem JSON")

    try:
        interpretar_resultados(gerador, criar_relatorio())
    except ValueError as erro:
        assert "JSON válido" in str(erro)
        print("Rejeição de JSON inválido: OK")
    else:
        raise AssertionError("JSON inválido foi aceito.")


def testar_tipo_invalido():
    resposta = {
        "summary": "Resumo.",
        "insights": [
            {
                "title": "Teste",
                "description": "Descrição.",
                "type": "inventado",
            }
        ],
    }

    gerador = FakeGerador(json.dumps(resposta))

    try:
        interpretar_resultados(gerador, criar_relatorio())
    except ValueError as erro:
        assert "Tipo de insight não permitido" in str(erro)
        print("Rejeição de tipo inválido: OK")
    else:
        raise AssertionError("Tipo de insight inválido foi aceito.")


if __name__ == "__main__":
    testar_insights_validos()
    testar_json_invalido()
    testar_tipo_invalido()

    print("\nTodos os testes passaram!")
