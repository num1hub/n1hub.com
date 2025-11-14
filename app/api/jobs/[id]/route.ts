import { NextRequest, NextResponse } from "next/server";
import { proxyJson } from "@/lib/engine-proxy";

interface Params {
  params: {
    id: string;
  };
}

export async function GET(_: NextRequest, { params }: Params) {
  const { body, status } = await proxyJson(`/jobs/${params.id}`);
  return NextResponse.json(body, { status });
}

export async function DELETE(_: NextRequest, { params }: Params) {
  const { body, status } = await proxyJson(`/jobs/${params.id}`, {
    method: "DELETE"
  });
  return NextResponse.json(body, { status });
}
