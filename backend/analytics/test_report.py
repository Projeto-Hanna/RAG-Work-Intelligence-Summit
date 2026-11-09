
"""Testes integrados do gerador de relatórios."""

import json

import pandas as pd

from analytics.report import gerar_relatorio


def main():
    df = pd.DataFrame({
        "produto": ["Notebook", "Mouse", "Notebook", "Mouse"],
        "quantidade": [2, 5, 3, 4],
        "valor": [1000.0, 100.0, 1500.0, 200.0],
        "data_venda": pd.to_datetime([
            "2026-01-10",
            "2026-01-15",
            "2026-02-10",
            "2026-02-15",
        ]),
    })

    relatorio = gerar_relatorio(
        dataframes={"vendas": df},
        titulo="Relatório de vendas",
        kpis=[
            {
                "label": "Faturamento total",
                "coluna": "valor",
                "operacao": "sum",
                "unidade": "R$",
            },
            {
                "label": "Quantidade de vendas",
                "coluna": "valor",
                "operacao": "count",
                "unidade": "vendas",
            },
        ],
        graficos=[
            {
                "tipo": "bar",
                "titulo": "Faturamento por produto",
                "coluna_grupo": "produto",
                "coluna_valor": "valor",
                "operacao": "sum",
            },
            {
                "tipo": "line",
                "titulo": "Evolução mensal",
                "coluna_data": "data_venda",
                "coluna_valor": "valor",
                "operacao": "sum",
                "frequencia": "ME",
            },
        ],
    )

    # Estrutura principal
    assert relatorio["title"] == "Relatório de vendas"
    assert len(relatorio["kpis"]) == 2
    assert len(relatorio["charts"]) == 2

    # KPIs
    assert relatorio["kpis"][0]["value"] == 2800.0
    assert relatorio["kpis"][0]["unit"] == "R$"
    assert relatorio["kpis"][1]["value"] == 4

    # Gráfico de barras
    barras = relatorio["charts"][0]

    assert barras["type"] == "bar"
    assert barras["labels"] == ["Notebook", "Mouse"]
    assert barras["values"] == [2500.0, 300.0]

    # Gráfico temporal
    linha = relatorio["charts"][1]

    assert linha["type"] == "line"
    assert linha["labels"] == ["2026-01", "2026-02"]
    assert linha["values"] == [1100.0, 1700.0]

    # Profiling
    assert relatorio["metadata"]["total_fontes"] == 1
    assert relatorio["metadata"]["profiling"]["vendas"]["total_registros"] == 4

    # Insights ainda serão preenchidos pelo LLM
    assert relatorio["insights"] == []

    # Compatibilidade com JSON
    json_relatorio = json.dumps(
        relatorio,
        ensure_ascii=False,
        allow_nan=False,
    )

    assert "Relatório de vendas" in json_relatorio

    print("Estrutura do relatório: OK")
    print("KPIs: OK")
    print("Gráfico de barras: OK")
    print("Gráfico temporal: OK")
    print("Profiling: OK")
    print("Serialização JSON: OK")
    print("\nTodos os testes passaram!")


if __name__ == "__main__":
    main()
