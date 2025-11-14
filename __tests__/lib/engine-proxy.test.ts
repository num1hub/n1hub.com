import { afterEach, describe, expect, it, vi } from "vitest";

import { proxyJson } from "@/lib/engine-proxy";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function createFetchResponse({
  status,
  body,
  contentType
}: {
  status: number;
  body: string;
  contentType?: string;
}) {
  return {
    status,
    headers: new Headers(contentType ? { "content-type": contentType } : {}),
    text: vi.fn().mockResolvedValue(body)
  };
}

describe("proxyJson", () => {
  it("parses JSON responses", async () => {
    const response = createFetchResponse({
      status: 200,
      body: JSON.stringify({ message: "ok" }),
      contentType: "application/json"
    });
    const fetchMock = vi.fn().mockResolvedValue(response);
    vi.stubGlobal("fetch", fetchMock);

    const result = await proxyJson("/status");

    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8000/status", {
      headers: { "Content-Type": "application/json" }
    });
    expect(result).toEqual({ body: { message: "ok" }, status: 200 });
  });

  it("wraps plain text responses in a detail object", async () => {
    const response = createFetchResponse({
      status: 502,
      body: "Bad gateway",
      contentType: "text/plain"
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));

    const result = await proxyJson("/status");

    expect(result).toEqual({ body: { detail: "Bad gateway" }, status: 502 });
  });

  it("falls back to detail when JSON cannot be parsed", async () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const response = createFetchResponse({
      status: 500,
      body: "{ invalid json",
      contentType: "application/json"
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));

    const result = await proxyJson("/status");

    expect(warnSpy).toHaveBeenCalled();
    expect(result).toEqual({ body: { detail: "{ invalid json" }, status: 500 });
  });

  it("returns null when the response body is empty", async () => {
    const response = createFetchResponse({ status: 204, body: "" });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));

    const result = await proxyJson("/status");

    expect(result).toEqual({ body: null, status: 204 });
  });
});
