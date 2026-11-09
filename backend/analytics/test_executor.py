
"""Testes de integração isolada do AgentExecutor."""

import unittest
from unittest.mock import Mock, patch

from agent.executor import AgentExecutor
from agent.schemas import AgentConfig


class TestAgentExecutor(unittest.TestCase):

    @patch("agent.executor.interpretar_resultados")
    @patch("agent.executor.gerar_relatorio")
    @patch("agent.executor.planejar_analise")
    @patch("agent.executor.carregar_fontes_estruturadas")
    @patch("agent.executor.formatar_fontes")
    def test_fluxo_analitico(
        self,
        mock_fontes,
        mock_carregar,
        mock_planejar,
        mock_relatorio,
        mock_interpretar,
    ):
        agente = AgentConfig(
            id="agente-teste",
            name="Agente Analítico",
            purpose="Criar relatórios e KPIs",
            tone="Profissional",
            instructions="Analise os dados e gere relatórios.",
            rag_enabled=False,
        )

        gerador = Mock()

        dataframes = {"vendas.csv:dados": Mock()}
        plano = {
            "titulo": "Relatório de vendas",
            "kpis": [],
            "graficos": [],
        }
        relatorio = {
            "title": "Relatório de vendas",
            "kpis": [],
            "charts": [],
            "insights": [],
            "sources": ["vendas.csv:dados"],
        }

        mock_carregar.return_value = dataframes
        mock_planejar.return_value = plano
        mock_relatorio.return_value = relatorio
        mock_interpretar.return_value = {
            "summary": "As vendas apresentaram resultados positivos.",
            "insights": [
                {
                    "title": "Resultado positivo",
                    "description": "O desempenho foi favorável.",
                    "type": "positive",
                }
            ],
        }
        mock_fontes.return_value = []

        executor = AgentExecutor()

        with patch.object(
            executor,
            "obter_gerador",
            return_value=gerador,
        ):
            resultado = executor.executar(
                agente=agente,
                mensagem="Gere um relatório de vendas.",
                provedor="gemini",
            )

        self.assertEqual(resultado["agent_id"], "agente-teste")
        self.assertEqual(
            resultado["response"],
            "As vendas apresentaram resultados positivos.",
        )
        self.assertIn("report", resultado)
        self.assertEqual(
            resultado["report"]["insights"][0]["type"],
            "positive",
        )
        self.assertEqual(
            resultado["sources"],
            ["vendas.csv:dados"],
        )

        mock_carregar.assert_called_once_with("agente-teste")
        mock_planejar.assert_called_once()
        mock_relatorio.assert_called_once()
        mock_interpretar.assert_called_once()


if __name__ == "__main__":
    unittest.main()
