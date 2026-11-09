
"""Montagem de relatórios analíticos estruturados."""

from typing import Any

import pandas as pd

from analytics.metrics import (
    calcular_metrica,
    agrupar_dados,
    gerar_serie_temporal,
)
from analytics.profiling import analisar_conjunto


def criar_kpi(
    dataframe: pd.DataFrame,
    label: str,
    coluna: str,
    operacao: str,
    unidade: str | None = None,
) -> dict[str, Any]:
    """Cria um KPI a partir de um cálculo validado."""

    resultado = calcular_metrica(
        dataframe=dataframe,
        coluna=coluna,
        operacao=operacao,
    )

    return {
        "label": label,
        "value": resultado["valor"],
        "unit": unidade,
        "metadata": {
            "coluna": coluna,
            "operacao": operacao,
            "registros_considerados": resultado["registros_considerados"],
        },
    }


def criar_grafico_barras(
    dataframe: pd.DataFrame,
    titulo: str,
    coluna_grupo: str,
    coluna_valor: str,
    operacao: str = "sum",
    limite: int = 20,
) -> dict[str, Any]:
    """Prepara os dados de um gráfico de barras."""

    resultado = agrupar_dados(
        dataframe=dataframe,
        coluna_grupo=coluna_grupo,
        coluna_valor=coluna_valor,
        operacao=operacao,
        limite=limite,
    )

    return {
        "type": "bar",
        "title": titulo,
        "labels": resultado["categorias"],
        "values": resultado["valores"],
        "metadata": {
            "coluna_grupo": coluna_grupo,
            "coluna_valor": coluna_valor,
            "operacao": operacao,
        },
    }


def criar_grafico_temporal(
    dataframe: pd.DataFrame,
    titulo: str,
    coluna_data: str,
    coluna_valor: str,
    operacao: str = "sum",
    frequencia: str = "ME",
) -> dict[str, Any]:
    """Prepara os dados de um gráfico de linha temporal."""

    resultado = gerar_serie_temporal(
        dataframe=dataframe,
        coluna_data=coluna_data,
        coluna_valor=coluna_valor,
        operacao=operacao,
        frequencia=frequencia,
    )

    return {
        "type": "line",
        "title": titulo,
        "labels": resultado["categorias"],
        "values": resultado["valores"],
        "metadata": {
            "coluna_data": coluna_data,
            "coluna_valor": coluna_valor,
            "operacao": operacao,
            "frequencia": frequencia,
        },
    }


def gerar_relatorio(
    dataframes: dict[str, pd.DataFrame],
    titulo: str,
    kpis: list[dict[str, Any]],
    graficos: list[dict[str, Any]],
    resumo: str = "",
) -> dict[str, Any]:
    """
    Monta um relatório estruturado.

    Os KPIs e gráficos são calculados pelo Python.
    Resumo e insights podem ser preenchidos posteriormente pelo LLM.
    """

    if not dataframes:
        raise ValueError("Nenhum conjunto de dados foi fornecido.")

    kpis_calculados = []
    graficos_calculados = []

    for nome_dataframe, dataframe in dataframes.items():

        for configuracao in kpis:
            if configuracao.get("fonte", nome_dataframe) != nome_dataframe:
                continue

            kpis_calculados.append(
                criar_kpi(
                    dataframe=dataframe,
                    label=configuracao["label"],
                    coluna=configuracao["coluna"],
                    operacao=configuracao["operacao"],
                    unidade=configuracao.get("unidade"),
                )
            )

        for configuracao in graficos:
            if configuracao.get("fonte", nome_dataframe) != nome_dataframe:
                continue

            tipo = configuracao["tipo"]

            if tipo == "bar":
                grafico = criar_grafico_barras(
                    dataframe=dataframe,
                    titulo=configuracao["titulo"],
                    coluna_grupo=configuracao["coluna_grupo"],
                    coluna_valor=configuracao["coluna_valor"],
                    operacao=configuracao.get("operacao", "sum"),
                    limite=configuracao.get("limite", 20),
                )

            elif tipo == "line":
                grafico = criar_grafico_temporal(
                    dataframe=dataframe,
                    titulo=configuracao["titulo"],
                    coluna_data=configuracao["coluna_data"],
                    coluna_valor=configuracao["coluna_valor"],
                    operacao=configuracao.get("operacao", "sum"),
                    frequencia=configuracao.get("frequencia", "ME"),
                )

            else:
                raise ValueError(
                    f"Tipo de gráfico não suportado: {tipo}"
                )

            graficos_calculados.append(grafico)

    perfil = analisar_conjunto(dataframes)

    return {
        "title": titulo,
        "summary": resumo,
        "kpis": kpis_calculados,
        "charts": graficos_calculados,
        "insights": [],
        "sources": list(dataframes.keys()),
        "metadata": {
            "total_fontes": len(dataframes),
            "profiling": perfil,
        },
    }
