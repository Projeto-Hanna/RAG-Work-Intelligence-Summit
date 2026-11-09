import { NextRequest } from "next/server";

const BACKEND_URL =
  process.env.BACKEND_URL || "http://127.0.0.1:8000";

type RouteContext = {
  params: Promise<{
    agentId: string;
    documentId: string;
  }>;
};

export async function POST(
  _request: NextRequest,
  context: RouteContext
) {
  try {
    const { agentId, documentId } = await context.params;

    if (!/^\d+$/.test(documentId)) {
      return Response.json(
        { detail: "Identificador de documento inválido." },
        { status: 400 }
      );
    }

    const response = await fetch(
      `${BACKEND_URL}/api/agents/${encodeURIComponent(agentId)}/documents/${documentId}/index`,
      {
        method: "POST",
        cache: "no-store",
      }
    );

    const data = await response.json();

    return Response.json(data, { status: response.status });
  } catch {
    return Response.json(
      { detail: "Não foi possível indexar o documento." },
      { status: 502 }
    );
  }
}