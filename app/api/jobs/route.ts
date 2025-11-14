import { NextResponse } from "next/server";
import { proxyJson } from "@/lib/engine-proxy";

export async function GET() {
  const { body, status } = await proxyJson("/jobs");
  return NextResponse.json(body, { status });
}
