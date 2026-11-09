
"""Teste de integração isolada do fluxo analítico."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

from agent.executor import AgentExecutor
from agent.schemas import AgentConfig
from analytics.loader import carregar_arquivo


class TestAnalyticsFlow(unittest.TestCase):

    @patch("agent.executor.interpretar_resultados")
    @patch("agent.executor.planejar_analise")
    @patch("agent.executor.carregar_fontes_estruturadas")
    def test_fluxo_com_calculos_reais(
        self,
        mock_carregar,
        mock_planejar,
        mock_interpretar,
    ):
        with tempfile.TemporaryDirectory() as diretorio:

            caminho_csv = Path(diretorio) / "vendas.csv"

            caminho_csv.write_text(
                "produto,quantidade,valor_total\n"
                "Notebook,2,6000\n"
                "Mouse,5,500\n"
                "Teclado,3,900\n"
                "Notebook,1,3000\n",
                encoding="utf-8",
            )

            # Carregamento real do CSV.
            tabelas = carregar_arquivo(caminho_csv)

            dataframes = {
                f"{caminho_csv.name}:{nome_tabela}": dataframe
                for nome_tabela, dataframe in tabelas.items()
            }

            mock_carregar.return_value = dataframes


            # Planejamento fixo: não utiliza LLM.
            mock_planejar.return_value = {
                "titulo": "Relatório de vendas",
                "kpis": [
                    {
                        "fonte": "vendas.csv:vendas",
                        "label": "Faturamento total",
                        "coluna": "valor_total",
                        "operacao": "sum",
                        "unidade": "R$",
                    },
                    {
                        "fonte": "vendas.csv:vendas",
                        "label": "Quantidade média",
                        "coluna": "quantidade",
                        "operacao": "mean",
                        "unidade": "unidades",
                    },
                ],
                "graficos": [
                    {
                        "fonte": "vendas.csv:vendas",
                        "tipo": "bar",
                        "titulo": "Faturamento por produto",
                        "coluna_grupo": "produto",
                        "coluna_valor": "valor_total",
                        "operacao": "sum",
                    }
                ],
            }

            # Interpretação simulada: não utiliza LLM.
            mock_interpretar.return_value = {
                "summary": "Relatório de vendas calculado com sucesso.",
                "insights": [
                    {
                        "title": "Destaque de faturamento",
                        "description": "Notebook apresentou o maior faturamento.",
                        "type": "positive",
                    }
                ],
            }

            agente = AgentConfig(
                id="agente-teste",
                name="Agente Analítico",
                purpose="Criar relatórios e KPIs",
                tone="Profissional",
                instructions="Analise os dados e gere relatórios.",
                rag_enabled=False,
            )

            executor = AgentExecutor()

            with patch.object(
                executor,
                "obter_gerador",
                return_value=Mock(),
            ):
                resultado = executor.executar(
                    agente=agente,
                    mensagem="Gere um relatório de vendas.",
                    provedor="gemini",
                )

            relatorio = resultado["report"]

            # Verificações do fluxo.
            self.assertEqual(resultado["agent_id"], "agente-teste")
            self.assertIn("report", resultado)

            # Verificações dos cálculos reais.
            self.assertEqual(relatorio["kpis"][0]["value"], 10400)
            self.assertEqual(relatorio["kpis"][1]["value"], 2.75)

            grafico = relatorio["charts"][0]

            self.assertEqual(grafico["type"], "bar")
            self.assertEqual(
                grafico["labels"],
                ["Notebook", "Teclado", "Mouse"],
            )
            self.assertEqual(
                grafico["values"],
                [9000, 900, 500],
            )

            # Verificações da interpretação simulada.
            self.assertEqual(
                relatorio["summary"],
                "Relatório de vendas calculado com sucesso.",
            )
            self.assertEqual(
                relatorio["insights"][0]["type"],
                "positive",
            )

            mock_carregar.assert_called_once_with("agente-teste")
            mock_planejar.assert_called_once()
            mock_interpretar.assert_called_once()

            print("Carregamento real do CSV: OK")
            print("Cálculo de KPIs: OK")
            print("Geração de gráfico: OK")
            print("Integração com AgentExecutor: OK")
            print("Interpretação simulada: OK")


if __name__ == "__main__":
    unittest.main()
