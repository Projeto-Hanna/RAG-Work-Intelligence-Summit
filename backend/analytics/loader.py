
"""Carregamento de arquivos estruturados para análises."""

from functools import lru_cache
from pathlib import Path

import pandas as pd


@lru_cache(maxsize=8)
def _carregar_arquivo_cached(
    caminho_resolvido: str,
    _mtime_ns: int,
    _tamanho: int,
) -> dict[str, pd.DataFrame]:
    """Lê do disco e faz parsing dos DataFrames mantendo em cache LRU."""

    arquivo = Path(caminho_resolvido)
    extensao = arquivo.suffix.lower()

    if extensao == ".csv":
        return carregar_csv(arquivo)

    if extensao == ".xlsx":
        return carregar_xlsx(arquivo)

    raise ValueError(
        f"Formato não suportado para análise: {extensao}"
    )


def limpar_cache_arquivos() -> None:
    """Descarta os DataFrames em cache (ex.: após excluir um documento)."""

    _carregar_arquivo_cached.cache_clear()


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
    """Carrega um CSV ou XLSX com cache por mtime e retorna cópias seguras."""

    arquivo_path = Path(arquivo)

    if not arquivo_path.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo_path}")

    extensao = arquivo_path.suffix.lower()
    if extensao not in {".csv", ".xlsx"}:
        raise ValueError(
            f"Formato não suportado para análise: {extensao}"
        )

    stat = arquivo_path.stat()
    caminho_resolvido = str(arquivo_path.resolve())

    tabelas_cached = _carregar_arquivo_cached(
        caminho_resolvido,
        stat.st_mtime_ns,
        stat.st_size,
    )

    # Retorna cópias defensivas para proteger os DataFrames originais no cache
    return {
        nome: df.copy()
        for nome, df in tabelas_cached.items()
    }
