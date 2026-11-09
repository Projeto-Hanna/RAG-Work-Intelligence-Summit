
"""Análise exploratória e identificação de características dos dados."""

import pandas as pd


def identificar_tipo_coluna(coluna: pd.Series) -> str:
    """Identifica o tipo de informação predominante na coluna."""

    if pd.api.types.is_bool_dtype(coluna):
        return "boolean"

    if pd.api.types.is_numeric_dtype(coluna):
        return "numeric"

    if pd.api.types.is_datetime64_any_dtype(coluna):
        return "datetime"

    valores = coluna.dropna()

    if valores.empty:
        return "empty"

    # Tenta identificar datas armazenadas como texto.
    if valores.dtype == object:
        datas = pd.to_datetime(
            valores,
            errors="coerce",
            dayfirst=True,
            format="mixed",
        )

        if datas.notna().mean() >= 0.8:
            return "datetime"

    # Identifica colunas categóricas.
    cardinalidade = valores.nunique()
    proporcao = cardinalidade / len(valores)

    if cardinalidade <= 30 or proporcao <= 0.05:
        return "categorical"

    return "text"


def analisar_coluna(coluna: pd.Series) -> dict:
    """Gera estatísticas e características de uma coluna."""

    tipo = identificar_tipo_coluna(coluna)

    resultado = {
        "tipo": tipo,
        "valores_ausentes": int(coluna.isna().sum()),
        "valores_unicos": int(coluna.nunique()),
        "percentual_ausente": round(
            coluna.isna().mean() * 100, 2
        ),
    }

    valores = coluna.dropna()

    if tipo == "numeric":
        resultado["estatisticas"] = {
            "media": round(float(valores.mean()), 2),
            "mediana": round(float(valores.median()), 2),
            "minimo": float(valores.min()),
            "maximo": float(valores.max()),
            "desvio_padrao": round(float(valores.std()), 2)
            if len(valores) > 1 else 0,
        }

    elif tipo == "categorical":
        resultado["categorias_mais_frequentes"] = {
            str(chave): int(valor)
            for chave, valor in valores.value_counts().head(10).items()
        }

    elif tipo == "datetime":
        datas = pd.to_datetime(
            valores,
            errors="coerce",
            dayfirst=True,
        ).dropna()

        if not datas.empty:
            resultado["periodo"] = {
                "inicio": str(datas.min()),
                "fim": str(datas.max()),
            }

    return resultado


def analisar_dataframe(dataframe: pd.DataFrame) -> dict:
    """Gera um perfil estatístico completo de um DataFrame."""

    if dataframe.empty:
        raise ValueError("Não é possível analisar um DataFrame vazio.")

    colunas = {
        str(nome): analisar_coluna(dataframe[nome])
        for nome in dataframe.columns
    }

    return {
        "total_registros": int(len(dataframe)),
        "total_colunas": int(len(dataframe.columns)),
        "registros_duplicados": int(
            dataframe.duplicated().sum()
        ),
        "colunas": colunas,
    }


def analisar_conjunto(
    dataframes: dict[str, pd.DataFrame],
) -> dict:
    """Analisa todas as tabelas de um arquivo ou conjunto de arquivos."""

    if not dataframes:
        raise ValueError("Nenhum conjunto de dados foi fornecido.")

    return {
        nome: analisar_dataframe(dataframe)
        for nome, dataframe in dataframes.items()
    }
