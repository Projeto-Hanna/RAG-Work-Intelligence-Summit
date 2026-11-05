
from agent.prompt import montar_mensagens

from config import TOP_K
from llm import Gerador
from retriever import buscar, formatar_fontes


class AgentExecutor:
    """Executa agentes utilizando LLM e, opcionalmente, RAG."""

    def __init__(self):
        self.gerador = None

    def executar(
        self,
        agente,
        mensagem,
        historico=None,
        gemini_api_key: str | None = None,
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

        if gemini_api_key:
            gerador = Gerador(
                usar_lora=False,
                api_key=gemini_api_key,
            )
        else:
            if self.gerador is None:
                self.gerador = Gerador(usar_lora=False)

            gerador = self.gerador

        resposta = gerador.gerar(mensagens)

        return {
            "agent_id": agente.id,
            "agent_name": agente.name,
            "response": resposta,
            "sources": formatar_fontes(resultados),
            "rag_enabled": agente.rag_enabled,
        }
