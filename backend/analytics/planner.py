
"""Planejamento e validação de análises solicitadas pelo usuário."""

import json
import re
from typing import Any

import pandas as pd

from analytics.metrics import OPERACOES


TIPOS_GRAFICOS = {"bar", "line"}


def montar_prompt_planejamento(
    mensagem: str,
    dataframes: dict[str, pd.DataFrame],
) -> list[dict[str, str]]:
    """Monta as mensagens para o LLM planejar uma análise."""

    fontes = {}

    for nome, dataframe in dataframes.items():
        fontes[nome] = {
            str(coluna): str(dataframe[coluna].dtype)
            for coluna in dataframe.columns
        }

    system_prompt = """
Você é um planejador de análises de dados.

Sua tarefa é transformar solicitações do usuário em planos
de análise estruturados.

REGRAS:
- Retorne exclusivamente um JSON válido.
- Não calcule métricas nem invente resultados.
- Utilize somente fontes e colunas disponíveis.
- Escolha operações compatíveis com os tipos das colunas.
- Para gráficos, utilize somente os tipos bar e line.
- Gráficos de linha devem utilizar uma coluna de datas.
- Não crie filtros ou operações que não foram solicitados.
- Se não houver dados suficientes, retorne listas vazias.
- Não execute código, SQL ou comandos.

REGRAS OBRIGATÓRIAS:
- As operações permitidas são exclusivamente:
  sum, mean, count, min, max, median, nunique.
- Nunca utilize avg. Para médias, utilize mean.
- Gráficos de barras devem utilizar group_column.
- Gráficos de linhas devem utilizar column_data.
- Gráficos de linhas devem utilizar uma coluna de datas.
- Não misture os campos group_column e column_data.

ESTRUTURA OBRIGATÓRIA:

{
  "title": "Título do relatório",
  "kpis": [
    {
      "source": "nome da fonte",
      "label": "Nome do indicador",
      "column": "nome da coluna",
      "operation": "sum",
      "unit": null
    }
  ],
  "charts": [
    {
      "source": "nome da fonte",
      "type": "bar",
      "title": "Título do gráfico",
      "group_column": "categoria",
      "value_column": "valor",
      "operation": "sum"
    }
  ]
}
""".strip()

    user_prompt = f"""
FONTES DISPONÍVEIS:

{json.dumps(fontes, ensure_ascii=False, indent=2)}

SOLICITAÇÃO DO USUÁRIO:

{mensagem}
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def extrair_json(resposta: str) -> dict[str, Any]:
    """Extrai e interpreta o JSON retornado pelo LLM."""

    if not resposta or not resposta.strip():
        raise ValueError("O LLM retornou uma resposta vazia.")

    conteudo = resposta.strip()

    # Remove blocos Markdown, caso existam.
    conteudo = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        conteudo,
        flags=re.IGNORECASE,
    ).strip()

    try:
        resultado = json.loads(conteudo)
    except json.JSONDecodeError as erro:
        raise ValueError(
            "O LLM não retornou um JSON válido."
        ) from erro

    if not isinstance(resultado, dict):
        raise ValueError("O plano deve ser um objeto JSON.")

    return resultado


def validar_plano(
    plano: dict[str, Any],
    dataframes: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    """Valida fontes, colunas, operações e tipos de gráficos."""

    if not isinstance(plano.get("title"), str) or not plano["title"].strip():
        raise ValueError("O plano precisa possuir um título válido.")

    kpis = plano.get("kpis")
    graficos = plano.get("charts")

    if not isinstance(kpis, list) or not isinstance(graficos, list):
        raise ValueError("KPIs e gráficos precisam ser listas.")

    if not kpis and not graficos:
        raise ValueError("O plano não contém análises.")

    kpis_validados = []
    graficos_validados = []

    for kpi in kpis:
        if not isinstance(kpi, dict):
            raise ValueError("Configuração de KPI inválida.")

        fonte = kpi.get("source")
        coluna = kpi.get("column")
        operacao = kpi.get("operation")

        if fonte not in dataframes:
            raise ValueError(f"Fonte não encontrada: {fonte}")

        dataframe = dataframes[fonte]

        if coluna not in dataframe.columns:
            raise ValueError(f"Coluna não encontrada: {coluna}")

        if operacao not in OPERACOES:
            raise ValueError(f"Operação não permitida: {operacao}")

        if operacao in {"sum", "mean", "median"}:
            if not pd.api.types.is_numeric_dtype(dataframe[coluna]):
                raise ValueError(
                    f"A operação '{operacao}' exige coluna numérica."
                )

        label = kpi.get("label")

        if not isinstance(label, str) or not label.strip():
            raise ValueError("KPI precisa possuir um nome válido.")

        unidade = kpi.get("unit")

        if unidade is not None and not isinstance(unidade, str):
            raise ValueError("A unidade do KPI precisa ser texto ou null.")

        kpis_validados.append({
            "fonte": fonte,
            "label": label.strip(),
            "coluna": coluna,
            "operacao": operacao,
            "unidade": unidade,
        })

    for grafico in graficos:
        if not isinstance(grafico, dict):
            raise ValueError("Configuração de gráfico inválida.")

        fonte = grafico.get("source")
        tipo = grafico.get("type")
        operacao = grafico.get("operation", "sum")

        if fonte not in dataframes:
            raise ValueError(f"Fonte não encontrada: {fonte}")

        if tipo not in TIPOS_GRAFICOS:
            raise ValueError(f"Tipo de gráfico não permitido: {tipo}")

        dataframe = dataframes[fonte]

        if operacao not in OPERACOES:
            raise ValueError(f"Operação não permitida: {operacao}")

        titulo = grafico.get("title")

        if not isinstance(titulo, str) or not titulo.strip():
            raise ValueError("Gráfico precisa possuir um título válido.")

        coluna_valor = grafico.get("value_column")

        if coluna_valor not in dataframe.columns:
            raise ValueError(
                f"Coluna não encontrada: {coluna_valor}"
            )

        if operacao in {"sum", "mean", "median"}:
            if not pd.api.types.is_numeric_dtype(dataframe[coluna_valor]):
                raise ValueError(
                    f"A operação '{operacao}' exige coluna numérica."
                )

        if tipo == "bar":
            coluna_grupo = grafico.get("group_column")

            if coluna_grupo not in dataframe.columns:
                raise ValueError(
                    f"Coluna de agrupamento inválida: {coluna_grupo}"
                )

            graficos_validados.append({
                "fonte": fonte,
                "tipo": "bar",
                "titulo": titulo.strip(),
                "coluna_grupo": coluna_grupo,
                "coluna_valor": coluna_valor,
                "operacao": operacao,
            })

        elif tipo == "line":
            coluna_data = grafico.get("column_data")

            if coluna_data not in dataframe.columns:
                raise ValueError(
                    f"Coluna de datas inválida: {coluna_data}"
                )

            if not pd.api.types.is_datetime64_any_dtype(
                dataframe[coluna_data]
            ):
                raise ValueError(
                    f"A coluna '{coluna_data}' precisa conter datas "
                    "convertidas."
                )

            graficos_validados.append({
                "fonte": fonte,
                "tipo": "line",
                "titulo": titulo.strip(),
                "coluna_data": coluna_data,
                "coluna_valor": coluna_valor,
                "operacao": operacao,
                "frequencia": "ME",
            })

    return {
        "titulo": plano["title"].strip(),
        "kpis": kpis_validados,
        "graficos": graficos_validados,
    }


def planejar_analise(
    gerador,
    mensagem: str,
    dataframes: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    """Solicita, interpreta e valida um plano de análise."""

    if not mensagem.strip():
        raise ValueError("A solicitação de análise está vazia.")

    if not dataframes:
        raise ValueError("Nenhuma fonte de dados foi fornecida.")

    mensagens = montar_prompt_planejamento(
        mensagem=mensagem,
        dataframes=dataframes,
    )

    resposta = gerador.gerar(
        mensagens,
        max_novos_tokens=4096,
        temperatura=0.1,
    )
    
    print("\n[DEBUG PLANNER] Tamanho da resposta:", len(resposta))
    print("\n[DEBUG PLANNER] Final da resposta:")
    print(repr(resposta[-2000:]))
    
    plano = extrair_json(resposta)

    return validar_plano(
        plano=plano,
        dataframes=dataframes,
    )
