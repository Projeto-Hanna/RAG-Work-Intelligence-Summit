
from agent.schemas import AgentConfig


def formatar_contexto(trechos: list[str]) -> str:
    """Formata os documentos recuperados pelo RAG."""

    if not trechos:
        return "Nenhum contexto documental foi fornecido."

    return "\n\n".join(
        f"[Documento {i}]\n{trecho.strip()}"
        for i, trecho in enumerate(trechos, start=1)
    )


def montar_mensagens(
    agente: AgentConfig,
    mensagem: str,
    trechos: list[str] | None = None,
    historico: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """
    Monta as mensagens para o LLM com base nas configurações do agente.

    Combina:
    - Identidade e finalidade do agente.
    - Tom de voz.
    - Instruções personalizadas.
    - Contexto recuperado pelo RAG.
    - Histórico da conversa.
    """

    trechos = trechos or []
    historico = historico or []

    system_prompt = f"""
Você é {agente.name}.

FINALIDADE:
{agente.purpose}

TOM DE VOZ:
{agente.tone}

INSTRUÇÕES:
{agente.instructions}

REGRAS:
- Responda em português do Brasil.
- Seja coerente com sua finalidade e suas instruções.
- Não invente informações.
- Quando utilizar documentos recuperados, priorize as informações presentes neles.
- Se os documentos não contiverem a informação solicitada, informe essa limitação.
- Diferencie claramente informações dos documentos de inferências próprias.
- Não afirme ter consultado documentos quando nenhum contexto foi fornecido.
""".strip()

    mensagens = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    # Janela deslizante: mantém até as últimas 50 mensagens do histórico
    historico_recente = historico[-50:] if len(historico) > 40 else historico

    # Adiciona o histórico anterior. O histórico enviado ao LLM precisa
    # começar por uma mensagem do usuário (exigência da API Anthropic),
    # então mensagens do assistente no início da janela são descartadas.
    encontrou_usuario = False

    for item in historico_recente:
        papel = item.get("role")
        conteudo = item.get("content", "").strip()

        if papel in ("user", "assistant") and conteudo:
            if papel == "user":
                encontrou_usuario = True
            elif not encontrou_usuario:
                continue

            mensagens.append({
                "role": papel,
                "content": conteudo,
            })

    # Adiciona o contexto e a pergunta atual.
    contexto = formatar_contexto(trechos)

    mensagem_usuario = f"""
CONTEXTO DOS DOCUMENTOS:
{contexto}

MENSAGEM DO USUÁRIO:
{mensagem.strip()}
""".strip()

    mensagens.append({
        "role": "user",
        "content": mensagem_usuario,
    })

    return mensagens
