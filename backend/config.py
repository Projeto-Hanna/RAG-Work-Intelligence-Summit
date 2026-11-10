
"""Configuração central do AgentLab."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env antes de acessá-las.
RAIZ = Path(__file__).parent
load_dotenv(RAIZ / ".env")

# Pastas e arquivos
PASTA_BASE = RAIZ / "base"
PASTA_DB = RAIZ / "db"
PASTA_ADAPTADORES = RAIZ / "adapters"
ADAPTADOR_LORA = PASTA_ADAPTADORES / "instagram"
ARQUIVO_EXEMPLOS = RAIZ / "data" / "exemplos.jsonl"
PASTA_DATABASE = RAIZ / "database"
ARQUIVO_DATABASE = PASTA_DATABASE / "agentlab.db"

# Bases de conhecimento por agente
PASTA_DATA = RAIZ / "data"

PASTA_BASE_COMPARTILHADA = PASTA_DATA / "shared_test"
PASTA_DOCUMENTOS_COMPARTILHADOS = (
    PASTA_BASE_COMPARTILHADA / "documents"
)
PASTA_DB_COMPARTILHADO = PASTA_BASE_COMPARTILHADA / "chroma"

PASTA_AGENTES = PASTA_DATA / "agents"

# Indexação e recuperação (RAG)
MODELO_EMBEDDINGS = "intfloat/multilingual-e5-small"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
TOP_K = 4

# Provedor padrão e ambiente de execução
ENV = os.getenv("ENV", "development").strip().lower()
IS_PRODUCTION = ENV == "production"
BACKEND_API_TOKEN = os.getenv("BACKEND_API_TOKEN", "").strip()

_default_providers = (
    "gemini,openai,anthropic"
    if IS_PRODUCTION
    else "gemini,openai,anthropic,llama"
)
ENABLED_PROVIDERS = tuple(
    p.strip().lower()
    for p in os.getenv("ENABLED_PROVIDERS", _default_providers).split(",")
    if p.strip()
)

LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "gemini" if IS_PRODUCTION else "llama",
).lower()

# Chaves de API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Modelos dos provedores
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_MODEL = os.getenv(
    "ANTHROPIC_MODEL",
    "claude-3-5-haiku-latest",
)

# Modelo local
MODELO_LLM = os.getenv(
    "MODELO_LLM",
    "Qwen/Qwen2.5-1.5B-Instruct",
)

# Parâmetros de geração
MAX_NOVOS_TOKENS = int(
    os.getenv("MAX_NOVOS_TOKENS", "1024")
)
TEMPERATURA = float(
    os.getenv("TEMPERATURA", "0.3")
)

# Regras do conteúdo
TOM_DE_VOZ = "claro, próximo e direto, sem formalidades"
LIMITE_LEGENDA = 2200
MAX_HASHTAGS = 5

# Treinamento LoRA
LORA_R = 8
LORA_ALPHA = 16
LORA_DROPOUT = 0.05
EPOCAS = 3
TAXA_APRENDIZADO = 2e-4
