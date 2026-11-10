function normalizarBackendUrl(raw?: string): string {
  const valor = raw?.trim().replace(/\/+$/, "");
  if (!valor) return "http://127.0.0.1:8000";
  if (!/^https?:\/\//i.test(valor)) {
    return `http://${valor}`;
  }
  return valor;
}

const BACKEND_URL = normalizarBackendUrl(process.env.BACKEND_URL);
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

export async function POST(request: Request) {
  const targetUrl = `${BACKEND_URL}/api/agents/chat`;

  try {
    const body = await request.json();

    const response = await fetch(targetUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(BACKEND_API_TOKEN
          ? { "X-Backend-Token": BACKEND_API_TOKEN }
          : {}),
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    const text = await response.text();
    let data: unknown;
    try {
      data = JSON.parse(text);
    } catch {
      console.error(
        `[POST /api/agents/chat] Resposta não-JSON (${response.status}):`,
        text
      );
      return Response.json(
        {
          detail: `Backend respondeu com status ${response.status} (formato inesperado).`,
        },
        { status: response.status || 502 }
      );
    }

    return Response.json(data, {
      status: response.status,
    });
  } catch (error) {
    const diagnostico = extrairCausaErro(error, targetUrl);
    console.error(
      "[POST /api/agents/chat] Falha de conexão com o backend:",
      diagnostico,
      error
    );

    return Response.json(
      {
        detail: `Não foi possível conectar ao backend: ${diagnostico}`,
      },
      { status: 502 }
    );
  }
}
