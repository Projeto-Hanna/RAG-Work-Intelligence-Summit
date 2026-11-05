import logging

from functools import lru_cache

from fastapi import APIRouter, HTTPException

from agent.executor import AgentExecutor
from agent.schemas import ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


@lru_cache(maxsize=1)
def obter_executor():
    """Reutiliza o executor entre as requisições."""
    return AgentExecutor()


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
        raise HTTPException(
            status_code=503,
            detail=f"Base de conhecimento indisponível: {erro}",
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
