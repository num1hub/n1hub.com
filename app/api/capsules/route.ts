import { NextRequest, NextResponse } from "next/server";
import { proxyJson } from "@/lib/engine-proxy";

export async function GET(request: NextRequest) {
  const query = request.nextUrl.search;
  const { body, status } = await proxyJson(`/capsules${query}`);
  return NextResponse.json(body, { status });
}
