const ENGINE_BASE_URL = process.env.ENGINE_BASE_URL ?? "http://127.0.0.1:8000";

export async function engineRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${ENGINE_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Engine request failed (${res.status}): ${detail}`);
  }

  return (await res.json()) as T;
}
