
"""Cálculos determinísticos de métricas e séries para gráficos."""

from typing import Any

import pandas as pd


OPERACOES = {
    "sum",
    "mean",
    "count",
    "min",
    "max",
    "median",
    "nunique",
}


def validar_coluna(
    dataframe: pd.DataFrame,
    coluna: str,
) -> None:
    """Verifica se uma coluna existe."""

    if coluna not in dataframe.columns:
        raise ValueError(f"Coluna não encontrada: {coluna}")


def validar_operacao(
    dataframe: pd.DataFrame,
    coluna: str,
    operacao: str,
) -> None:
    """Valida a compatibilidade entre coluna e operação."""

    validar_coluna(dataframe, coluna)

    if operacao not in OPERACOES:
        raise ValueError(f"Operação não suportada: {operacao}")

    if operacao in {"sum", "mean", "median"}:
        if not pd.api.types.is_numeric_dtype(dataframe[coluna]):
            raise ValueError(
                f"A operação '{operacao}' exige uma coluna numérica."
            )


def calcular_metrica(
    dataframe: pd.DataFrame,
    coluna: str,
    operacao: str,
) -> dict[str, Any]:
    """Calcula uma métrica sobre uma coluna."""

    if dataframe.empty:
        raise ValueError("Não é possível calcular métricas em dados vazios.")

    validar_operacao(dataframe, coluna, operacao)

    serie = dataframe[coluna].dropna()

    if operacao == "sum":
        valor = serie.sum()

    elif operacao == "mean":
        valor = serie.mean()

    elif operacao == "count":
        valor = serie.count()

    elif operacao == "min":
        valor = serie.min()

    elif operacao == "max":
        valor = serie.max()

    elif operacao == "median":
        valor = serie.median()

    elif operacao == "nunique":
        valor = serie.nunique()

    else:
        raise ValueError(f"Operação não suportada: {operacao}")

    if pd.isna(valor):
        valor = None
    elif hasattr(valor, "item"):
        valor = valor.item()

    if isinstance(valor, (int, float)):
        valor = round(valor, 2)

    return {
        "coluna": coluna,
        "operacao": operacao,
        "valor": valor,
        "registros_considerados": int(serie.count()),
    }


def calcular_metricas(
    dataframe: pd.DataFrame,
    metricas: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Calcula várias métricas sobre o mesmo DataFrame."""

    resultados = []

    for metrica in metricas:
        resultados.append(
            calcular_metrica(
                dataframe=dataframe,
                coluna=metrica["coluna"],
                operacao=metrica["operacao"],
            )
        )

    return resultados


def agrupar_dados(
    dataframe: pd.DataFrame,
    coluna_grupo: str,
    coluna_valor: str,
    operacao: str = "sum",
    limite: int = 20,
) -> dict[str, Any]:
    """Agrupa dados e calcula uma agregação por categoria."""

    if dataframe.empty:
        raise ValueError("Não há dados para agrupar.")

    validar_coluna(dataframe, coluna_grupo)
    validar_operacao(dataframe, coluna_valor, operacao)

    if limite < 1:
        raise ValueError("O limite deve ser maior que zero.")

    dados = dataframe[[coluna_grupo, coluna_valor]].copy()
    dados = dados.dropna(subset=[coluna_grupo])

    if operacao == "nunique":
        agrupado = dados.groupby(
            coluna_grupo,
            observed=True,
        )[coluna_valor].nunique()

    else:
        agrupado = dados.groupby(
            coluna_grupo,
            observed=True,
        )[coluna_valor].agg(operacao)

    agrupado = agrupado.sort_values(
        ascending=False,
        na_position="last",
    ).head(limite)

    return {
        "coluna_grupo": coluna_grupo,
        "coluna_valor": coluna_valor,
        "operacao": operacao,
        "categorias": [
            str(valor) for valor in agrupado.index
        ],
        "valores": [
            round(float(valor), 2)
            for valor in agrupado.values
        ],
    }


def calcular_variacao(
    valor_atual: float,
    valor_anterior: float,
) -> dict[str, Any]:
    """Calcula a variação absoluta e percentual entre dois valores."""

    diferenca = valor_atual - valor_anterior

    if valor_anterior == 0:
        percentual = None
    else:
        percentual = round(
            (diferenca / abs(valor_anterior)) * 100,
            2,
        )

    return {
        "valor_atual": valor_atual,
        "valor_anterior": valor_anterior,
        "diferenca": round(diferenca, 2),
        "variacao_percentual": percentual,
    }


def gerar_serie_temporal(
    dataframe: pd.DataFrame,
    coluna_data: str,
    coluna_valor: str,
    operacao: str = "sum",
    frequencia: str = "ME",
) -> dict[str, Any]:
    """Agrupa valores por período para alimentar gráficos temporais."""

    if dataframe.empty:
        raise ValueError("Não há dados para gerar a série temporal.")

    validar_coluna(dataframe, coluna_data)
    validar_operacao(dataframe, coluna_valor, operacao)

    if not pd.api.types.is_datetime64_any_dtype(dataframe[coluna_data]):
        raise ValueError(
            f"A coluna '{coluna_data}' precisa conter datas convertidas."
        )

    dados = dataframe[[coluna_data, coluna_valor]].dropna().copy()

    if dados.empty:
        raise ValueError("Não existem registros válidos para a série.")

    dados = dados.set_index(coluna_data)

    if operacao == "nunique":
        serie = dados[coluna_valor].resample(frequencia).nunique()
    else:
        serie = dados[coluna_valor].resample(frequencia).agg(operacao)

    return {
        "coluna_data": coluna_data,
        "coluna_valor": coluna_valor,
        "operacao": operacao,
        "frequencia": frequencia,
        "categorias": [
            data.strftime("%Y-%m")
            for data in serie.index
        ],
        "valores": [
            round(float(valor), 2)
            for valor in serie.values
        ],
    }
