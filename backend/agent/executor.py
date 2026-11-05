
from agent.prompt import montar_mensagens

from config import TOP_K
from llm import Gerador
from retriever import buscar, formatar_fontes


class AgentExecutor:
    """Executa agentes utilizando LLM e, opcionalmente, RAG."""

    def __init__(self):
        self.geradores = {}

    def executar(
        self,
        agente,
        mensagem,
        historico=None,
        provedor="gemini",
        api_key: str | None = None,
    ):
        resultados = []

        if agente.rag_enabled:
            resultados = buscar(
                mensagem,
                k=agente.top_k or TOP_K,
            )

        trechos = [
            documento.page_content
            for documento, _ in resultados
        ]

        mensagens = montar_mensagens(
            agente=agente,
            mensagem=mensagem,
            trechos=trechos,
            historico=historico,
        )

        if api_key:
            gerador = Gerador(
                usar_lora=False,
                api_key=api_key,
                provedor=provedor,
            )
        else:
            if provedor not in self.geradores:
                self.geradores[provedor] = Gerador(
                    usar_lora=(provedor == "llama"),
                    provedor=provedor,
                )

            gerador = self.geradores[provedor]

        resposta = gerador.gerar(mensagens)

        return {
            "agent_id": agente.id,
            "agent_name": agente.name,
            "response": resposta,
            "sources": formatar_fontes(resultados),
            "rag_enabled": agente.rag_enabled,
            "provider": provedor,
        }
