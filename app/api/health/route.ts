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

function formatFetchError(error: unknown, targetUrl: string): string {
  if (!(error instanceof Error)) {
    return `Erro desconhecido ao acessar ${targetUrl}`;
  }

  const cause = (error as Error & { cause?: { code?: string; message?: string } }).cause;
  const code = cause?.code ? ` [${cause.code}]` : "";
  const causeMsg = cause?.message ? ` (${cause.message})` : "";

  return `${error.message}${code}${causeMsg} -> ${targetUrl}`;
}

export async function GET() {
  const start = Date.now();
  const targetUrl = `${BACKEND_URL}/health`;

  try {
    const response = await fetch(targetUrl, {
      method: "GET",
      headers: BACKEND_API_TOKEN
        ? { "X-Backend-Token": BACKEND_API_TOKEN }
        : undefined,
      cache: "no-store",
    });

    const text = await response.text();
    let backendData: unknown = text;
    try {
      backendData = JSON.parse(text);
    } catch {
      // mantém texto bruto
    }

    return Response.json(
      {
        ok: response.ok,
        status: response.status,
        latency_ms: Date.now() - start,
        configured_backend_url: BACKEND_URL,
        using_default_localhost: !process.env.BACKEND_URL,
        has_backend_token: Boolean(BACKEND_API_TOKEN),
        backend_response: backendData,
      },
      { status: response.ok ? 200 : 502 }
    );
  } catch (error) {
    const diagnostic = formatFetchError(error, targetUrl);
    console.error("[GET /api/health] Falha ao conectar ao backend:", diagnostic, error);

    return Response.json(
      {
        ok: false,
        latency_ms: Date.now() - start,
        configured_backend_url: BACKEND_URL,
        using_default_localhost: !process.env.BACKEND_URL,
        has_backend_token: Boolean(BACKEND_API_TOKEN),
        error: diagnostic,
      },
      { status: 502 }
    );
  }
}

