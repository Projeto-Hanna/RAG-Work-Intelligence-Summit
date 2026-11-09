"""Gerenciamento dos diretórios das bases de conhecimento."""

import re
from pathlib import Path

from config import (
    PASTA_AGENTES,
    PASTA_DOCUMENTOS_COMPARTILHADOS,
    PASTA_DB_COMPARTILHADO,
)


def obter_diretorios_base(
    agent_id: str,
    knowledge_base_type: str,
) -> tuple[Path, Path]:

    if not re.fullmatch(r"[a-zA-Z0-9_-]+", agent_id):
        raise ValueError("Identificador de agente inválido.")

    if knowledge_base_type == "test":
        return (
            PASTA_DOCUMENTOS_COMPARTILHADOS,
            PASTA_DB_COMPARTILHADO,
        )

    if knowledge_base_type == "custom":
        pasta_agente = PASTA_AGENTES / agent_id

        return (
            pasta_agente / "documents",
            pasta_agente / "chroma",
        )

    raise ValueError("Tipo de base de conhecimento inválido.")