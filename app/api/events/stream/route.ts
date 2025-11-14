import { NextRequest } from "next/server";

const ENGINE_BASE_URL = process.env.ENGINE_BASE_URL ?? "http://127.0.0.1:8000";

export async function GET(_: NextRequest) {
  const response = await fetch(`${ENGINE_BASE_URL}/events/stream`, {
    headers: {
      "Cache-Control": "no-cache",
      Connection: "keep-alive"
    }
  });

  if (!response.ok) {
    return new Response("SSE connection failed", { status: response.status });
  }

  return new Response(response.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive"
    }
  });
}
