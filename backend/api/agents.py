from fastapi import APIRouter, HTTPException

from agent.executor import AgentExecutor
from agent.schemas import ChatRequest


router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.post("/chat")
def conversar(request: ChatRequest):
    """Recebe uma mensagem e retorna a resposta do agente."""

    try:
        executor = AgentExecutor()

        resultado = executor.executar(
            agente=request.agent,
            mensagem=request.message,
            historico=request.history,
            gemini_api_key=(
                request.gemini_api_key.get_secret_value()
                if request.gemini_api_key
                else None
            ),
        )

        return resultado

    except FileNotFoundError as erro:
        raise HTTPException(
            status_code=503,
            detail=f"Base de conhecimento indisponível: {erro}",
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro ao executar o agente.",
        )