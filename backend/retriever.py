"""Recuperação de documentos usando ChromaDB."""

import sys
from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma

from config import PASTA_DB, TOP_K
from embeddings import get_embeddings


@lru_cache(maxsize=10)
def carregar_db(pasta_db: str = str(PASTA_DB)):
    caminho = Path(pasta_db)

    if not caminho.exists():
        raise FileNotFoundError(
            f"Banco vetorial não encontrado em '{caminho}'. "
            "Indexe os documentos primeiro."
        )

    return Chroma(
        persist_directory=str(caminho),
        embedding_function=get_embeddings(),
    )


def buscar(
    pergunta: str,
    k: int = TOP_K,
    distancia_maxima: float | None = None,
    pasta_db: str = str(PASTA_DB),
):
    """Retorna documentos e suas distâncias."""

    caminho = Path(pasta_db)

    if not (caminho / "chroma.sqlite3").is_file():
        return []

    resultados = carregar_db(str(caminho)).similarity_search_with_score(
        pergunta,
        k=k,
    )

    if distancia_maxima is not None:
        resultados = [
            (doc, distancia)
            for doc, distancia in resultados
            if distancia <= distancia_maxima
        ]

    return resultados


def formatar_fontes(resultados) -> list[str]:
    """Formata as fontes dos documentos recuperados."""

    fontes = []

    for doc, _ in resultados:
        arquivo = Path(doc.metadata.get("source", "?")).name
        pagina = doc.metadata.get("page")

        fontes.append(
            f"{arquivo}, p. {pagina + 1}"
            if isinstance(pagina, int)
            else arquivo
        )

    return fontes


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]) or input("Pergunta: ")
    achados = buscar(pergunta)

    for (doc, distancia), fonte in zip(
        achados,
        formatar_fontes(achados),
    ):
        print(f"\n--- distância {distancia:.3f} | {fonte}")
        print(doc.page_content[:400])