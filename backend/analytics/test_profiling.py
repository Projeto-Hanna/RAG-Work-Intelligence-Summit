
"""Testes do módulo de análise exploratória."""

import pandas as pd

from analytics.profiling import (
    analisar_dataframe,
    analisar_conjunto,
    identificar_tipo_coluna,
)


def main():
    df = pd.DataFrame({
        "produto": ["Notebook", "Mouse", "Notebook", "Teclado"],
        "quantidade": [2, 5, 3, 4],
        "valor": [3500.0, 120.0, 3500.0, 250.0],
        "data_venda": [
            "01/10/2026",
            "02/10/2026",
            "03/10/2026",
            "04/10/2026",
        ],
        "observacao": ["OK", None, "OK", "Pendente"],
    })

    perfil = analisar_dataframe(df)

    assert perfil["total_registros"] == 4
    assert perfil["total_colunas"] == 5
    assert perfil["registros_duplicados"] == 0

    assert perfil["colunas"]["produto"]["tipo"] == "categorical"
    assert perfil["colunas"]["quantidade"]["tipo"] == "numeric"
    assert perfil["colunas"]["valor"]["tipo"] == "numeric"
    assert perfil["colunas"]["data_venda"]["tipo"] == "datetime"

    assert perfil["colunas"]["quantidade"]["estatisticas"]["media"] == 3.5
    assert perfil["colunas"]["quantidade"]["estatisticas"]["minimo"] == 2
    assert perfil["colunas"]["quantidade"]["estatisticas"]["maximo"] == 5

    assert perfil["colunas"]["observacao"]["valores_ausentes"] == 1
    assert perfil["colunas"]["observacao"]["percentual_ausente"] == 25.0

    conjunto = analisar_conjunto({"vendas": df})

    assert "vendas" in conjunto
    assert conjunto["vendas"]["total_registros"] == 4

    assert identificar_tipo_coluna(pd.Series([True, False])) == "boolean"

    print("Total de registros:", perfil["total_registros"])
    print("Total de colunas:", perfil["total_colunas"])
    print("Tipos identificados:")

    for nome, dados in perfil["colunas"].items():
        print(f"  {nome}: {dados['tipo']}")

    print("\nTodos os testes passaram!")


if __name__ == "__main__":
    main()
