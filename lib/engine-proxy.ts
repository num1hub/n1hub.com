const ENGINE_BASE_URL = process.env.ENGINE_BASE_URL ?? "http://127.0.0.1:8000";

function parseResponseBody(text: string, contentType: string | null) {
  if (!text) {
    return null;
  }

  const isJson = contentType?.includes("application/json");

  try {
    return JSON.parse(text);
  } catch (error) {
    if (isJson) {
      console.warn("Failed to parse JSON response from engine", error);
    }
  }

  return { detail: text };
}

export async function proxyJson(path: string, init?: RequestInit) {
  const res = await fetch(`${ENGINE_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });
  const text = await res.text();
  const body = parseResponseBody(text, res.headers.get("content-type"));
  return { body, status: res.status };
}
