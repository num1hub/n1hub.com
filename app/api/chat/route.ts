import { NextRequest, NextResponse } from "next/server";
import { proxyJson } from "@/lib/engine-proxy";

export async function POST(request: NextRequest) {
  const payload = await request.json();
  const { body, status } = await proxyJson("/chat", {
    method: "POST",
    body: JSON.stringify(payload)
  });
  return NextResponse.json(body, { status });
}
