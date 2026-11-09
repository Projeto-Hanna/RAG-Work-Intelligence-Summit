
"""Geração de resumos e insights a partir de relatórios calculados."""

import json
import re
from typing import Any


def montar_mensagens_insights(
    relatorio: dict[str, Any],
    contexto_rag: list[str] | None = None,
) -> list[dict[str, str]]:
    """Prepara os resultados e o contexto para interpretação pelo LLM."""

    dados = {
        "title": relatorio.get("title"),
        "kpis": relatorio.get("kpis", []),
        "charts": relatorio.get("charts", []),
        "sources": relatorio.get("sources", []),
    }

    contexto = contexto_rag or []

    system_prompt = """
Você é um analista de dados especializado em relatórios gerenciais.

Sua tarefa é interpretar resultados já calculados e produzir insights.

REGRAS:
- Utilize exclusivamente os resultados fornecidos.
- Não invente valores, métricas, tendências ou causas.
- Diferencie fatos observados de hipóteses.
- Utilize o contexto documental apenas para contextualizar os resultados.
- Não apresente informações do contexto como se fossem métricas calculadas.
- Se os dados forem insuficientes, informe essa limitação.
- Escreva de maneira objetiva e profissional.
- Retorne exclusivamente um JSON válido.

FORMATO OBRIGATÓRIO:

{
    "summary": "Resumo executivo do relatório.",
    "insights": [
        {
            "title": "Título do insight",
            "description": "Explicação baseada nos resultados.",
            "type": "positive"
        }
    ]
}

O campo type deve ser um destes valores:
positive, negative, neutral ou attention.
""".strip()

    user_prompt = f"""
RESULTADOS CALCULADOS:

{json.dumps(dados, ensure_ascii=False, indent=2, default=str)}

CONTEXTO DOCUMENTAL:

{json.dumps(contexto, ensure_ascii=False, indent=2, default=str)}
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def interpretar_resultados(
    gerador,
    relatorio: dict[str, Any],
    contexto_rag: list[str] | None = None,
) -> dict[str, Any]:
    """Gera resumo e insights sem recalcular métricas."""

    mensagens = montar_mensagens_insights(
        relatorio=relatorio,
        contexto_rag=contexto_rag,
    )

    resposta = gerador.gerar(
        mensagens,
        max_novos_tokens=1024,
        temperatura=0.2,
    )

    conteudo = resposta.strip()

    conteudo = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        conteudo,
        flags=re.IGNORECASE,
    ).strip()

    try:
        resultado = json.loads(conteudo)
    except json.JSONDecodeError as erro:
        raise ValueError(
            "O LLM não retornou um JSON válido para os insights."
        ) from erro

    if not isinstance(resultado, dict):
        raise ValueError("A resposta dos insights precisa ser um objeto JSON.")

    resumo = resultado.get("summary")
    insights = resultado.get("insights")

    if not isinstance(resumo, str):
        raise ValueError("O resumo retornado pelo LLM é inválido.")

    if not isinstance(insights, list):
        raise ValueError("A lista de insights retornada é inválida.")

    tipos_permitidos = {
        "positive",
        "negative",
        "neutral",
        "attention",
    }

    insights_validados = []

    for insight in insights:
        if not isinstance(insight, dict):
            raise ValueError("Foi encontrado um insight inválido.")

        titulo = insight.get("title")
        descricao = insight.get("description")
        tipo = insight.get("type")

        if not isinstance(titulo, str) or not titulo.strip():
            raise ValueError("Um insight possui título inválido.")

        if not isinstance(descricao, str) or not descricao.strip():
            raise ValueError("Um insight possui descrição inválida.")

        if tipo not in tipos_permitidos:
            raise ValueError(f"Tipo de insight não permitido: {tipo}")

        insights_validados.append({
            "title": titulo.strip(),
            "description": descricao.strip(),
            "type": tipo,
        })

    return {
        "summary": resumo.strip(),
        "insights": insights_validados,
    }
