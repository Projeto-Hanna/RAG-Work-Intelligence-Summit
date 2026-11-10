import { NextRequest } from "next/server";

const BACKEND_URL =
  process.env.BACKEND_URL?.trim().replace(/\/+$/, "") ||
  "http://127.0.0.1:8000";
const BACKEND_API_TOKEN =
  process.env.BACKEND_API_TOKEN?.trim() || "";

export const maxDuration = 60;

function extrairCausaErro(error: unknown, url: string): string {
  if (!(error instanceof Error)) {
    return `Erro desconhecido ao conectar em ${url}`;
  }

  const cause = (
    error as Error & { cause?: { code?: string; message?: string } }
  ).cause;
  const codigo = cause?.code || error.name || "FETCH_ERROR";
  const detalheCausa = cause?.message ? ` (${cause.message})` : "";

  if (!process.env.BACKEND_URL) {
    return `BACKEND_URL não está definida na Vercel (usando fallback ${BACKEND_URL}). Faça Redeploy após configurar as variáveis.`;
  }

  return `[${codigo}] ${error.message}${detalheCausa} ao tentar acessar ${url}`;
}

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
  const { agentId, documentId } = await context.params;

  if (!/^\d+$/.test(documentId)) {
    return Response.json(
      { detail: "Identificador de documento inválido." },
      { status: 400 }
    );
  }

  const targetUrl = `${BACKEND_URL}/api/agents/${encodeURIComponent(agentId)}/documents/${documentId}/index`;

  try {
    const response = await fetch(targetUrl, {
      method: "POST",
      headers: BACKEND_API_TOKEN
        ? { "X-Backend-Token": BACKEND_API_TOKEN }
        : undefined,
      cache: "no-store",
    });

    const data = await response.json();

    return Response.json(data, { status: response.status });
  } catch (error) {
    const diagnostico = extrairCausaErro(error, targetUrl);
    console.error("[POST index] Falha:", diagnostico, error);

    return Response.json(
      { detail: `Não foi possível indexar o documento: ${diagnostico}` },
      { status: 502 }
    );
  }
}
