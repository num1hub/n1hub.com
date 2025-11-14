import { NextRequest, NextResponse } from "next/server";
import { proxyJson } from "@/lib/engine-proxy";

interface Params {
  params: {
    id: string;
  };
}

export async function GET(_: NextRequest, { params }: Params) {
  const { body, status } = await proxyJson(`/capsules/${params.id}`);
  return NextResponse.json(body, { status });
}

export async function PATCH(request: NextRequest, { params }: Params) {
  const payload = await request.json();
  const { body, status } = await proxyJson(`/capsules/${params.id}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
  return NextResponse.json(body, { status });
}
