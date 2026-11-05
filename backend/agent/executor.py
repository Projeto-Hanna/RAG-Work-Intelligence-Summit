
from agent.schemas import AgentConfig
from agent.prompt import montar_mensagens

from config import TOP_K
from llm import Gerador
from retriever import buscar, formatar_fontes


class AgentExecutor:
    """Executa agentes utilizando LLM e, opcionalmente, RAG."""

    def __init__(self):
        # Não aplica o LoRA especializado em posts do Instagram.
        self.gerador = Gerador(usar_lora=False)

    def executar(
        self,
        agente: AgentConfig,
        mensagem: str,
        historico: list[dict[str, str]] | None = None,
    ) -> dict:
        """Executa uma mensagem e retorna resposta e fontes."""

        resultados = []

        # Recupera documentos somente se o RAG estiver ativado.
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

        resposta = self.gerador.gerar(mensagens)

        return {
            "agent_id": agente.id,
            "agent_name": agente.name,
            "response": resposta,
            "sources": formatar_fontes(resultados),
            "rag_enabled": agente.rag_enabled,
        }
