
from typing import Literal

from pydantic import BaseModel, Field, SecretStr


AGENT_ID_PATTERN = r"^[a-zA-Z0-9_-]+$"


class AgentConfig(BaseModel):
    """Configurações de um agente criado no AgentLab."""

    id: str = Field(min_length=1, max_length=100, pattern=AGENT_ID_PATTERN)
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

    provider: Literal[
        "gemini",
        "openai",
        "anthropic",
        "llama",
    ] = "gemini"

    api_key: SecretStr | None = None

class AgentRegistration(BaseModel):
    id: str = Field(min_length=1, max_length=100, pattern=AGENT_ID_PATTERN)
    name: str = Field(min_length=1, max_length=100)
    knowledge_base_type: Literal["test", "custom"] = "test"
