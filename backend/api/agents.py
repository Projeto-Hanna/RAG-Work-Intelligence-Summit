import logging
from functools import lru_cache

from fastapi import APIRouter, HTTPException

from agent.executor import AgentExecutor
from agent.schemas import ChatRequest, AgentRegistration
from database import cadastrar_agente

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


@lru_cache(maxsize=1)
def obter_executor():
    """Reutiliza o executor entre as requisições."""
    return AgentExecutor()

@router.post("/register")
def registrar_agente(request: AgentRegistration):
    try:
        cadastrar_agente(
            request.id,
            request.name,
            request.knowledge_base_type,
        )
        return {"message": "Agente cadastrado com sucesso."}

    except Exception:
        logger.exception("Erro ao cadastrar agente.")
        raise HTTPException(
            status_code=500,
            detail="Erro ao cadastrar agente.",
        )
@router.post("/chat")
def conversar(request: ChatRequest):
    """Recebe uma mensagem e retorna a resposta do agente."""

    try:
        executor = obter_executor()

        resultado = executor.executar(
            agente=request.agent,
            mensagem=request.message,
            historico=request.history,
            provedor=request.provider,
            api_key=(
                request.api_key.get_secret_value()
                if request.api_key
                else None
            ),
        )

        return resultado

    except FileNotFoundError as erro:
        logger.warning("Base de conhecimento indisponível: %s", erro)
        raise HTTPException(
            status_code=503,
            detail="Base de conhecimento indisponível. Indexe os documentos primeiro.",
        )

    except ValueError as erro:
        raise HTTPException(
            status_code=400,
            detail=str(erro),
        )

    except Exception:
        logger.exception("Erro inesperado ao executar o agente.")
        raise HTTPException(
            status_code=500,
            detail="Erro ao executar o agente.",
        )
