
"""Localização e carregamento de fontes estruturadas dos agentes."""

from pathlib import Path

from database import (
    obter_tipo_base_agente,
    listar_documentos_por_agente,
)
from knowledge_base import obter_diretorios_base
from analytics.loader import carregar_arquivo


AGENTE_BASE_COMPARTILHADA = "shared_test"

EXTENSOES_ANALITICAS = {".csv", ".xlsx"}


def carregar_fontes_estruturadas(
    agent_id: str,
) -> dict:
    """Carrega arquivos CSV/XLSX indexados e autorizados do agente."""

    tipo_base = obter_tipo_base_agente(agent_id)

    pasta_documentos, _ = obter_diretorios_base(
        agent_id,
        tipo_base,
    )

    document_agent_id = (
        AGENTE_BASE_COMPARTILHADA
        if tipo_base == "test"
        else agent_id
    )

    documentos = listar_documentos_por_agente(
        document_agent_id
    )

    dataframes = {}

    pasta_autorizada = pasta_documentos.resolve()

    for documento in documentos:

        if documento["status"] != "indexed":
            continue

        caminho = Path(documento["filepath"]).resolve()

        if not caminho.is_relative_to(pasta_autorizada):
            continue

        if caminho.suffix.lower() not in EXTENSOES_ANALITICAS:
            continue

        if not caminho.is_file():
            continue

        tabelas = carregar_arquivo(caminho)

        for nome_tabela, dataframe in tabelas.items():

            nome_fonte = f"{documento['filename']}:{nome_tabela}"

            dataframes[nome_fonte] = dataframe

    if not dataframes:
        raise ValueError(
            "Nenhum arquivo CSV ou XLSX indexado foi encontrado "
            "na base de conhecimento do agente."
        )

    return dataframes
