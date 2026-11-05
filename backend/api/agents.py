
from functools import lru_cache

from fastapi import APIRouter, HTTPException

from agent.executor import AgentExecutor
from agent.schemas import ChatRequest


router = APIRouter(prefix="/api/agents", tags=["agents"])


@lru_cache(maxsize=1)
def obter_executor() -> AgentExecutor:
    """Mantém uma única instância do executor durante a execução da API."""
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
        )

        return resultado

    except FileNotFoundError as erro:
        raise HTTPException(
            status_code=503,
            detail=f"Base de conhecimento indisponível: {erro}",
        )

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao executar o agente: {erro}",
        )
