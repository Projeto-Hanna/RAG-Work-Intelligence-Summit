
"""Testes das funções de cálculo de métricas."""

import pandas as pd

from analytics.metrics import (
    calcular_metrica,
    calcular_metricas,
    calcular_variacao,
    agrupar_dados,
    gerar_serie_temporal,
)


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

    # Métricas individuais
    assert calcular_metrica(df, "valor", "sum")["valor"] == 2800.0
    assert calcular_metrica(df, "valor", "mean")["valor"] == 700.0
    assert calcular_metrica(df, "valor", "count")["valor"] == 4
    assert calcular_metrica(df, "valor", "min")["valor"] == 100.0
    assert calcular_metrica(df, "valor", "max")["valor"] == 1500.0
    assert calcular_metrica(df, "valor", "median")["valor"] == 600.0
    assert calcular_metrica(df, "produto", "nunique")["valor"] == 2

    # Múltiplas métricas
    metricas = calcular_metricas(
        df,
        [
            {"coluna": "valor", "operacao": "sum"},
            {"coluna": "quantidade", "operacao": "mean"},
        ],
    )

    assert len(metricas) == 2
    assert metricas[0]["valor"] == 2800.0
    assert metricas[1]["valor"] == 3.5

    # Agrupamento por produto
    agrupamento = agrupar_dados(
        df,
        coluna_grupo="produto",
        coluna_valor="valor",
        operacao="sum",
    )

    assert agrupamento["categorias"] == ["Notebook", "Mouse"]
    assert agrupamento["valores"] == [2500.0, 300.0]

    # Variação percentual
    variacao = calcular_variacao(150.0, 100.0)

    assert variacao["diferenca"] == 50.0
    assert variacao["variacao_percentual"] == 50.0

    # Variação com valor anterior zero
    variacao_zero = calcular_variacao(100.0, 0.0)
    assert variacao_zero["variacao_percentual"] is None

    # Série temporal mensal
    serie = gerar_serie_temporal(
        df,
        coluna_data="data_venda",
        coluna_valor="valor",
        operacao="sum",
        frequencia="ME",
    )

    assert serie["categorias"] == ["2026-01", "2026-02"]
    assert serie["valores"] == [1100.0, 1700.0]

    # Validação de coluna inexistente
    try:
        calcular_metrica(df, "coluna_inexistente", "sum")
        raise AssertionError("Deveria rejeitar coluna inexistente.")
    except ValueError:
        pass

    # Validação de operação incompatível
    try:
        calcular_metrica(df, "produto", "mean")
        raise AssertionError("Deveria rejeitar média de texto.")
    except ValueError:
        pass

    print("Métricas individuais: OK")
    print("Múltiplas métricas: OK")
    print("Agrupamentos: OK")
    print("Variações: OK")
    print("Séries temporais: OK")
    print("Validações: OK")
    print("\nTodos os testes passaram!")


if __name__ == "__main__":
    main()
