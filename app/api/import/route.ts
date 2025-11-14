import { NextRequest, NextResponse } from "next/server";
import { proxyJson } from "@/lib/engine-proxy";

export async function POST(request: NextRequest) {
  const payload = await request.json();
  const idempotencyKey = request.headers.get("Idempotency-Key");

  const headers: Record<string, string> = {
    "Content-Type": "application/json"
  };

  if (idempotencyKey) {
    headers["Idempotency-Key"] = idempotencyKey;
  }

  const { body, status } = await proxyJson("/ingest", {
    method: "POST",
    body: JSON.stringify(payload),
    headers
  });

  return NextResponse.json(body, { status });
}
