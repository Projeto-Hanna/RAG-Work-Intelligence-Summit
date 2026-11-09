
"""Testes básicos do carregador de arquivos."""

import tempfile
from pathlib import Path

import pandas as pd

from analytics.loader import carregar_arquivo


def testar_csv(pasta: Path):
    arquivo = pasta / "vendas.csv"

    arquivo.write_text(
        "produto;quantidade;valor\n"
        "Notebook;2;3500.00\n"
        "Mouse;5;120.00\n",
        encoding="utf-8",
    )

    resultado = carregar_arquivo(arquivo)
    df = resultado["vendas"]

    assert len(df) == 2
    assert list(df.columns) == ["produto", "quantidade", "valor"]

    print("CSV carregado:", df.shape)


def testar_xlsx(pasta: Path):
    arquivo = pasta / "vendas.xlsx"

    df = pd.DataFrame({
        "produto": ["Notebook", "Mouse"],
        "quantidade": [2, 5],
        "valor": [3500.00, 120.00],
    })

    df.to_excel(arquivo, index=False)

    resultado = carregar_arquivo(arquivo)
    df_carregado = next(iter(resultado.values()))
    assert len(df_carregado) == 2
    assert "valor" in df_carregado.columns

    print("XLSX carregado:", df_carregado.shape)


def main():
    with tempfile.TemporaryDirectory() as diretorio:
        pasta = Path(diretorio)

        testar_csv(pasta)
        testar_xlsx(pasta)

    print("Todos os testes passaram!")


if __name__ == "__main__":
    main()
