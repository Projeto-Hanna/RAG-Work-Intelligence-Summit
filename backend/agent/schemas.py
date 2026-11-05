from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configurações de um agente criado no AgentLab."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=100)
    purpose: str = Field(min_length=1, max_length=500)
    tone: str = Field(min_length=1, max_length=200)
    instructions: str = Field(min_length=1, max_length=5000)

    rag_enabled: bool = True
    top_k: int = Field(default=4, ge=1, le=10)


class ChatRequest(BaseModel):
    """Mensagem enviada ao agente."""

    agent: AgentConfig
    message: str = Field(min_length=1, max_length=10000)
    history: list[dict[str, str]] = Field(default_factory=list)