
from agent.prompt import montar_mensagens

from config import TOP_K
from llm import Gerador
from retriever import buscar, formatar_fontes
from database import obter_tipo_base_agente
from knowledge_base import obter_diretorios_base

from analytics.data_source import carregar_fontes_estruturadas
from analytics.planner import planejar_analise
from analytics.report import gerar_relatorio
from analytics.insights import interpretar_resultados


class AgentExecutor:
    """Executa agentes utilizando LLM, RAG e análise de dados."""

    def __init__(self):
        self.geradores = {}

    def obter_gerador(
        self,
        provedor: str,
        api_key: str | None = None,
    ):
        """Obtém uma instância do gerador para o provedor escolhido."""

        if api_key:
            return Gerador(
                usar_lora=False,
                api_key=api_key,
                provedor=provedor,
            )

        if provedor not in self.geradores:
            self.geradores[provedor] = Gerador(
                usar_lora=(provedor == "llama"),
                provedor=provedor,
            )

        return self.geradores[provedor]

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
            tipo_base = obter_tipo_base_agente(agente.id)

            _, pasta_db = obter_diretorios_base(
                agente.id,
                tipo_base,
            )

            resultados = buscar(
                mensagem,
                k=agente.top_k or TOP_K,
                pasta_db=str(pasta_db),
            )

        trechos = [
            documento.page_content
            for documento, _ in resultados
        ]

        gerador = self.obter_gerador(
            provedor=provedor,
            api_key=api_key,
        )

        fontes = formatar_fontes(resultados)

        if agente.purpose == "Criar relatórios e KPIs":
            return self.executar_analise(
                agente=agente,
                mensagem=mensagem,
                gerador=gerador,
                contexto_rag=trechos,
                fontes_rag=fontes,
                provedor=provedor,
            )

        mensagens = montar_mensagens(
            agente=agente,
            mensagem=mensagem,
            trechos=trechos,
            historico=historico,
        )

        resposta = gerador.gerar(mensagens)

        return {
            "agent_id": agente.id,
            "agent_name": agente.name,
            "response": resposta,
            "sources": fontes,
            "rag_enabled": agente.rag_enabled,
            "provider": provedor,
        }

    def executar_analise(
        self,
        agente,
        mensagem,
        gerador,
        contexto_rag,
        fontes_rag,
        provedor,
    ):
        """Executa o fluxo de geração de relatórios e KPIs."""

        dataframes = carregar_fontes_estruturadas(agente.id)

        plano = planejar_analise(
            gerador=gerador,
            mensagem=mensagem,
            dataframes=dataframes,
        )

        relatorio = gerar_relatorio(
            dataframes=dataframes,
            titulo=plano["titulo"],
            kpis=plano["kpis"],
            graficos=plano["graficos"],
        )

        interpretacao = interpretar_resultados(
            gerador=gerador,
            relatorio=relatorio,
            contexto_rag=contexto_rag,
        )

        relatorio["summary"] = interpretacao["summary"]
        relatorio["insights"] = interpretacao["insights"]

        return {
            "agent_id": agente.id,
            "agent_name": agente.name,
            "response": relatorio["summary"],
            "report": relatorio,
            "sources": fontes_rag + list(dataframes.keys()),
            "rag_enabled": agente.rag_enabled,
            "provider": provedor,
        }
