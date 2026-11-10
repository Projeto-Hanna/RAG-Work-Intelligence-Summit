
const BACKEND_URL =
  process.env.BACKEND_URL || "http://127.0.0.1:8000";
const BACKEND_API_TOKEN =
  process.env.BACKEND_API_TOKEN || "";

export const maxDuration = 60;

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const response = await fetch(`${BACKEND_URL}/api/agents/chat`, {
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
