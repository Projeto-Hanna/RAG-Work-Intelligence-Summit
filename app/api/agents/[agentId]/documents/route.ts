import { NextRequest } from "next/server";

const BACKEND_URL =
  process.env.BACKEND_URL?.trim().replace(/\/+$/, "") ||
  "http://127.0.0.1:8000";
const BACKEND_API_TOKEN =
  process.env.BACKEND_API_TOKEN?.trim() || "";

export const maxDuration = 60;

function getAuthHeaders(): Record<string, string> {
  return BACKEND_API_TOKEN
    ? { "X-Backend-Token": BACKEND_API_TOKEN }
    : {};
}

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
  const agentId = await obterAgentId(context);
  const targetUrl = `${BACKEND_URL}/api/agents/${agentId}/documents`;

  try {
    const response = await fetch(targetUrl, {
      headers: getAuthHeaders(),
      cache: "no-store",
    });

    const data = await response.json();

    return Response.json(data, { status: response.status });
  } catch (error) {
    const diagnostico = extrairCausaErro(error, targetUrl);
    console.error("[GET documents] Falha:", diagnostico, error);

    return Response.json(
      { detail: `Não foi possível conectar ao backend: ${diagnostico}` },
      { status: 502 }
    );
  }
}

const ALLOWED_EXTENSIONS = [".pdf", ".csv", ".xlsx", ".json"];
const MAX_FILE_SIZE = 4 * 1024 * 1024;

// Enviar documentos para o agente
export async function POST(
  request: NextRequest,
  context: RouteContext
) {
  const agentId = await obterAgentId(context);
  const targetUrl = `${BACKEND_URL}/api/agents/${agentId}/documents`;

  try {
    const formData = await request.formData();
    const files = formData.getAll("files");

    if (!files || files.length === 0) {
      return Response.json(
        { detail: "Nenhum arquivo enviado." },
        { status: 400 }
      );
    }

    for (const item of files) {
      if (item instanceof File) {
        const ext = `.${item.name.split(".").pop()?.toLowerCase() || ""}`;
        if (!ALLOWED_EXTENSIONS.includes(ext)) {
          return Response.json(
            { detail: `Extensão não permitida para o arquivo ${item.name}. Permitidos: .pdf, .csv, .xlsx, .json` },
            { status: 400 }
          );
        }
        if (item.size > MAX_FILE_SIZE) {
          return Response.json(
            { detail: `O arquivo "${item.name}" excede o limite de 4 MB.` },
            { status: 413 }
          );
        }
      }
    }

    const response = await fetch(targetUrl, {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
      cache: "no-store",
    });

    const data = await response.json();

    return Response.json(data, { status: response.status });
  } catch (error) {
    const diagnostico = extrairCausaErro(error, targetUrl);
    console.error("[POST documents] Falha:", diagnostico, error);

    return Response.json(
      {
        detail: `Não foi possível enviar os documentos ao backend: ${diagnostico}`,
      },
      { status: 502 }
    );
  }
}

// Excluir documento do agente
export async function DELETE(
  request: NextRequest,
  context: RouteContext
) {
  const agentId = await obterAgentId(context);
  const documentId = request.nextUrl.searchParams.get("documentId");

  if (!documentId || !/^\d+$/.test(documentId)) {
    return Response.json(
      { detail: "Identificador de documento inválido." },
      { status: 400 }
    );
  }

  const targetUrl = `${BACKEND_URL}/api/agents/${agentId}/documents/${documentId}`;

  try {
    const response = await fetch(targetUrl, {
      method: "DELETE",
      headers: getAuthHeaders(),
      cache: "no-store",
    });

    const data = await response.json();

    return Response.json(data, { status: response.status });
  } catch (error) {
    const diagnostico = extrairCausaErro(error, targetUrl);
    console.error("[DELETE documents] Falha:", diagnostico, error);

    return Response.json(
      { detail: `Não foi possível excluir o documento: ${diagnostico}` },
      { status: 502 }
    );
  }
}
