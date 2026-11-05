
const BACKEND_URL =
  (globalThis as typeof globalThis & {
    process?: { env?: { BACKEND_URL?: string } };
  }).process?.env?.BACKEND_URL || "http://127.0.0.1:8000";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const response = await fetch(`${BACKEND_URL}/api/agents/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    const data = await response.json();

    return Response.json(data, {
      status: response.status,
    });
  } catch {
    return Response.json(
      {
        detail:
          "Não foi possível conectar ao backend. Verifique se o FastAPI está em execução.",
      },
      { status: 502 }
    );
  }
}
