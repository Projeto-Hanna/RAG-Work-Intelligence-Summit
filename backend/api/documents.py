
"""Rotas para gerenciamento de documentos dos agentes."""

from pathlib import Path
from uuid import uuid4

from index import indexar_documento

from fastapi import APIRouter, File, HTTPException, UploadFile

from database import (
    conectar,
    cadastrar_agente,
    obter_tipo_base_agente,
    registrar_documento,
)
from knowledge_base import obter_diretorios_base

router = APIRouter(
    prefix="/api/agents/{agent_id}/documents",
    tags=["documents"],
)

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".xlsx", ".json"}
MAX_FILE_SIZE = 50 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


def obter_contexto_base(agent_id: str):
    """Resolve o agente e os diretórios da sua base."""

    try:
        tipo_base = obter_tipo_base_agente(agent_id)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Agente não encontrado.",
        )

    if tipo_base == "test":
        document_agent_id = "shared_test"

        cadastrar_agente(
            document_agent_id,
            "Base compartilhada de testes",
            "test",
        )
    else:
        document_agent_id = agent_id

    pasta_documentos, _ = obter_diretorios_base(
        agent_id,
        tipo_base,
    )

    pasta_documentos.mkdir(parents=True, exist_ok=True)

    return document_agent_id, pasta_documentos


@router.get("")
def listar_documentos(agent_id: str):
    document_agent_id, _ = obter_contexto_base(agent_id)

    with conectar() as conexao:
        documentos = conexao.execute(
            """
            SELECT id, filename, filepath, status, created_at
            FROM documents
            WHERE agent_id = ?
            ORDER BY id DESC
            """,
            (document_agent_id,),
        ).fetchall()

    return {
        "documentos": [
            {
                "id": documento["id"],
                "nome": documento["filename"],
                "status": documento["status"],
                "data_criacao": documento["created_at"],
                "tamanho": (
                    Path(documento["filepath"]).stat().st_size
                    if Path(documento["filepath"]).exists()
                    else 0
                ),
            }
            for documento in documentos
        ]
    }


@router.post("")
async def enviar_documentos(
    agent_id: str,
    files: list[UploadFile] = File(...),
):
    document_agent_id, pasta_documentos = obter_contexto_base(agent_id)

    resultados = []

    for file in files:
        nome_original = Path(file.filename or "").name
        extensao = Path(nome_original).suffix.lower()

        if not nome_original or extensao not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo não permitido: {nome_original}",
            )

        nome_armazenado = f"{uuid4().hex}_{nome_original}"
        destino = pasta_documentos / nome_armazenado
        tamanho = 0

        try:
            with destino.open("wb") as output:
                while True:
                    chunk = await file.read(CHUNK_SIZE)

                    if not chunk:
                        break

                    tamanho += len(chunk)

                    if tamanho > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail=f"{nome_original} excede o limite de 50 MB.",
                        )

                    output.write(chunk)

            document_id = registrar_documento(
                agent_id=document_agent_id,
                filename=nome_original,
                filepath=str(destino),
                status="uploaded",
            )

            resultados.append({
                "id": document_id,
                "nome": nome_original,
                "tamanho": tamanho,
                "status": "uploaded",
            })

        except Exception:
            destino.unlink(missing_ok=True)
            raise

        finally:
            await file.close()

    return {
        "message": "Upload concluído.",
        "documentos": resultados,
    }


@router.delete("/{document_id}")
def excluir_documento(agent_id: str, document_id: int):
    document_agent_id, pasta_documentos = obter_contexto_base(agent_id)

    with conectar() as conexao:
        documento = conexao.execute(
            """
            SELECT id, filepath
            FROM documents
            WHERE id = ? AND agent_id = ?
            """,
            (document_id, document_agent_id),
        ).fetchone()

        if documento is None:
            raise HTTPException(
                status_code=404,
                detail="Documento não encontrado.",
            )

        caminho = Path(documento["filepath"])

        if caminho.parent.resolve() != pasta_documentos.resolve():
            raise HTTPException(
                status_code=403,
                detail="Caminho do documento inválido.",
            )

        if caminho.is_symlink():
            raise HTTPException(
                status_code=403,
                detail="Não é permitido excluir links simbólicos.",
            )

        if caminho.exists():
            caminho.unlink()

        conexao.execute(
            "DELETE FROM documents WHERE id = ?",
            (document_id,),
        )

    return {"message": "Documento excluído com sucesso."}

@router.post("/{document_id}/index")
def indexar_documento_api(agent_id: str, document_id: int):
    try:
        return indexar_documento(agent_id, document_id)

    except ValueError as erro:
        raise HTTPException(
            status_code=404,
            detail=str(erro),
        )

    except FileNotFoundError as erro:
        raise HTTPException(
            status_code=404,
            detail=str(erro),
        )

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao indexar documento: {erro}",
        )