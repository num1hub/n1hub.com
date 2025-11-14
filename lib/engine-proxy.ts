const ENGINE_BASE_URL = process.env.ENGINE_BASE_URL ?? "http://127.0.0.1:8000";

export async function proxyJson(path: string, init?: RequestInit) {
  const res = await fetch(`${ENGINE_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });
  const text = await res.text();
  const body = text ? JSON.parse(text) : null;
  return { body, status: res.status };
}
