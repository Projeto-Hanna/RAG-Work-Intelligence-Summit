
"""Carregamento de arquivos estruturados para análises."""

from pathlib import Path

import pandas as pd


def detectar_separador(arquivo: Path) -> tuple[str, str]:
    """Detecta o separador e o encoding de um CSV."""

    encodings = ["utf-8-sig", "cp1252", "latin-1"]

    for encoding in encodings:
        try:
            with arquivo.open("r", encoding=encoding) as entrada:
                amostra = entrada.read(8192)

            if not amostra.strip():
                raise ValueError("O arquivo CSV está vazio.")

            primeira_linha = amostra.splitlines()[0]

            separador = (
                ";"
                if primeira_linha.count(";") > primeira_linha.count(",")
                else ","
            )

            return separador, encoding

        except UnicodeDecodeError:
            continue

    raise ValueError("Não foi possível identificar o encoding do CSV.")


def carregar_csv(arquivo: Path) -> dict[str, pd.DataFrame]:
    """Carrega um CSV preservando e identificando os tipos dos dados."""

    separador, encoding = detectar_separador(arquivo)

    dataframe = pd.read_csv(
        arquivo,
        sep=separador,
        encoding=encoding,
        keep_default_na=True,
        on_bad_lines="error",
    )

    # Identifica e converte colunas com nomes relacionados a datas.
    for coluna in dataframe.columns:
        nome = str(coluna).strip().lower()

        if nome in {"data", "date", "datetime", "timestamp"}:
            dataframe[coluna] = pd.to_datetime(
                dataframe[coluna],
                errors="coerce",
                format="mixed",
            )

    return {arquivo.stem: dataframe}

def carregar_xlsx(arquivo: Path) -> dict[str, pd.DataFrame]:
    """Carrega todas as planilhas de um arquivo Excel."""

    planilhas = pd.read_excel(
        arquivo,
        sheet_name=None,
        engine="openpyxl",
    )

    # Identifica e converte colunas com nomes relacionados a datas.
    for dataframe in planilhas.values():
        for coluna in dataframe.columns:
            nome = str(coluna).strip().lower()

            if nome in {"data", "date", "datetime", "timestamp"}:
                dataframe[coluna] = pd.to_datetime(
                    dataframe[coluna],
                    errors="coerce",
                    format="mixed",
                )

    return planilhas


def carregar_arquivo(arquivo: str | Path) -> dict[str, pd.DataFrame]:
    """Carrega um CSV ou XLSX e retorna seus DataFrames."""

    arquivo = Path(arquivo)

    if not arquivo.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

    extensao = arquivo.suffix.lower()

    if extensao == ".csv":
        return carregar_csv(arquivo)

    if extensao == ".xlsx":
        return carregar_xlsx(arquivo)

    raise ValueError(
        f"Formato não suportado para análise: {extensao}"
    )
