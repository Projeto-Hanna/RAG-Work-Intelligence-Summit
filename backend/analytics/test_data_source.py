
"""Testes de carregamento e isolamento das fontes estruturadas."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from analytics.data_source import carregar_fontes_estruturadas


def main():
    with tempfile.TemporaryDirectory() as temporario:
        raiz = Path(temporario)

        pasta_documentos = raiz / "documents"
        pasta_documentos.mkdir()

        pasta_externa = raiz / "externo"
        pasta_externa.mkdir()

        # Arquivos de teste
        arquivo_csv = pasta_documentos / "vendas.csv"
        pd.DataFrame({
            "produto": ["Notebook", "Mouse"],
            "valor": [1000, 200],
        }).to_csv(arquivo_csv, index=False)

        arquivo_externo = pasta_externa / "privado.csv"
        pd.DataFrame({
            "valor": [9999],
        }).to_csv(arquivo_externo, index=False)

        arquivo_pdf = pasta_documentos / "manual.pdf"
        arquivo_pdf.write_text("Arquivo não analítico.")

        documentos = [
            {
                "filename": "vendas.csv",
                "filepath": str(arquivo_csv),
                "status": "indexed",
            },
            {
                "filename": "privado.csv",
                "filepath": str(arquivo_externo),
                "status": "indexed",
            },
            {
                "filename": "pendente.csv",
                "filepath": str(arquivo_csv),
                "status": "uploaded",
            },
            {
                "filename": "manual.pdf",
                "filepath": str(arquivo_pdf),
                "status": "indexed",
            },
        ]

        with (
            patch(
                "analytics.data_source.obter_tipo_base_agente",
                return_value="custom",
            ),
            patch(
                "analytics.data_source.obter_diretorios_base",
                return_value=(pasta_documentos, raiz / "chroma"),
            ),
            patch(
                "analytics.data_source.listar_documentos_por_agente",
                return_value=documentos,
            ) as consulta,
        ):
            resultado = carregar_fontes_estruturadas("agente_teste")

            # Somente o CSV autorizado deve ser carregado.
            assert len(resultado) == 1

            nome_fonte = "vendas.csv:vendas"
            assert nome_fonte in resultado

            dataframe = resultado[nome_fonte]

            assert len(dataframe) == 2
            assert dataframe["valor"].sum() == 1200

            # Verifica o identificador usado na consulta.
            consulta.assert_called_once_with("agente_teste")

        print("Carregamento de CSV: OK")
        print("Filtro de status: OK")
        print("Isolamento de diretório: OK")
        print("Filtro de extensão: OK")
        print("Consulta pelo agente: OK")
        print("\nTodos os testes passaram!")

        with (
            patch(
                "analytics.data_source.obter_tipo_base_agente",
                return_value="test",
            ),
            patch(
                "analytics.data_source.obter_diretorios_base",
                return_value=(pasta_documentos, raiz / "chroma"),
            ),
            patch(
                "analytics.data_source.listar_documentos_por_agente",
                return_value=documentos,
            ) as consulta,
        ):
            resultado = carregar_fontes_estruturadas("outro_agente")

            assert "vendas.csv:vendas" in resultado
            consulta.assert_called_once_with("shared_test")

        print("Base compartilhada shared_test: OK")

if __name__ == "__main__":
    main()

