
import { NextRequest } from "next/server";

const BACKEND_URL =
  process.env.BACKEND_URL || "http://127.0.0.1:8000";

type RouteContext = {
  params: Promise<{ agentId: string }>;
};

async function obterAgentId(context: RouteContext) {
  const { agentId } = await context.params;
  return encodeURIComponent(agentId);
}

// Listar documentos do agente
export async function GET(
  _request: NextRequest,
  context: RouteContext
) {
  try {
    const agentId = await obterAgentId(context);

    const response = await fetch(
      `${BACKEND_URL}/api/agents/${agentId}/documents`,
      { cache: "no-store" }
    );

    const data = await response.json();

    return Response.json(data, { status: response.status });
  } catch {
    return Response.json(
      { detail: "Não foi possível conectar ao backend." },
      { status: 502 }
    );
  }
}

// Enviar documentos para o agente
export async function POST(
  request: NextRequest,
  context: RouteContext
) {
  try {
    const agentId = await obterAgentId(context);
    const formData = await request.formData();

    const response = await fetch(
      `${BACKEND_URL}/api/agents/${agentId}/documents`,
      {
        method: "POST",
        body: formData,
        cache: "no-store",
      }
    );

    const data = await response.json();

    return Response.json(data, { status: response.status });
  } catch {
    return Response.json(
      { detail: "Não foi possível enviar os documentos ao backend." },
      { status: 502 }
    );
  }
}

// Excluir documento do agente
export async function DELETE(
  request: NextRequest,
  context: RouteContext
) {
  try {
    const agentId = await obterAgentId(context);
    const documentId = request.nextUrl.searchParams.get("documentId");

    if (!documentId || !/^\d+$/.test(documentId)) {
      return Response.json(
        { detail: "Identificador de documento inválido." },
        { status: 400 }
      );
    }

    const response = await fetch(
      `${BACKEND_URL}/api/agents/${agentId}/documents/${documentId}`,
      {
        method: "DELETE",
        cache: "no-store",
      }
    );

    const data = await response.json();

    return Response.json(data, { status: response.status });
  } catch {
    return Response.json(
      { detail: "Não foi possível excluir o documento." },
      { status: 502 }
    );
  }
}
