import type { Capsule, ChatRequestBody, ChatResponse, Job } from "@/lib/types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });

  if (!res.ok) {
    const detail = await res.text();
    const retryAfter = res.headers.get("Retry-After");
    const error: Error & { status?: number; retryAfter?: string } = new Error(
      res.status === 429
        ? `Rate limit exceeded. ${retryAfter ? `Retry after ${retryAfter} seconds.` : ""}`
        : `Request failed (${res.status}): ${detail}`
    );
    error.status = res.status;
    if (retryAfter) error.retryAfter = retryAfter;
    throw error;
  }

  return (await res.json()) as T;
}

export function listJobs() {
  return request<Job[]>("/api/jobs");
}

export function getJob(id: string) {
  return request<Job>(`/api/jobs/${id}`);
}

export function listCapsules(params?: { include_in_rag?: boolean }) {
  const query = params ? `?${new URLSearchParams(
        Object.entries(params).reduce<Record<string, string>>((acc, [key, value]) => {
          if (value !== undefined) {
            acc[key] = String(value);
          }
          return acc;
        }, {})
      ).toString()}` : "";
  return request<Capsule[]>(`/api/capsules${query}`);
}

export function getCapsule(id: string) {
  return request<Capsule>(`/api/capsules/${id}`);
}

export function toggleCapsule(id: string, include: boolean) {
  return request<Capsule>(`/api/capsules/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ include_in_rag: include })
  });
}

export function ingestMaterial(data: { title: string; content: string; tags: string[]; include_in_rag: boolean }) {
  return request<{ job_id: string }>("/api/import", {
    method: "POST",
    body: JSON.stringify(data)
  });
}

export function runChat(body: ChatRequestBody) {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify(body)
  });
}

export function cancelJob(id: string) {
  return request<{ status: string; job_id: string }>(`/api/jobs/${id}`, {
    method: "DELETE"
  });
}
