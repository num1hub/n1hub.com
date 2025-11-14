"use client";

import { useId, useState } from "react";
import { ingestMaterial } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { TextArea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useQueryClient } from "@tanstack/react-query";

export function UploadForm() {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags] = useState("capsule,knowledge");
  const [includeInRag, setIncludeInRag] = useState(true);
  const [status, setStatus] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const queryClient = useQueryClient();
  const titleId = useId();
  const tagsId = useId();
  const materialId = useId();

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setStatus(null);
    try {
      const tagList = tags
        .split(",")
        .map((tag) => tag.trim().toLowerCase())
        .filter(Boolean);
      const response = await ingestMaterial({ title, content, tags: tagList, include_in_rag: includeInRag });
      setStatus(`Job ${response.job_id} created`);
      setTitle("");
      setContent("");
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
    } catch (error) {
      const err = error as Error & { status?: number; retryAfter?: string };
      if (err.status === 429) {
        setStatus(`Rate limit exceeded. ${err.retryAfter ? `Please retry after ${err.retryAfter} seconds.` : "Please try again later."}`);
      } else {
        setStatus(`Upload failed: ${err.message}`);
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-2xl border border-white/10 bg-slate-900/60 p-5">
      <div className="flex flex-col gap-4">
        <div>
          <label htmlFor={titleId} className="text-sm font-semibold text-white">
            Title
          </label>
          <Input
            id={titleId}
            value={title}
            required
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Capsule title"
          />
        </div>
        <div>
          <label htmlFor={tagsId} className="text-sm font-semibold text-white">
            Tags
          </label>
          <Input
            id={tagsId}
            value={tags}
            onChange={(event) => setTags(event.target.value)}
            placeholder="comma,separated,tags"
          />
        </div>
        <div>
          <label htmlFor={materialId} className="text-sm font-semibold text-white">
            Material
          </label>
          <TextArea
            id={materialId}
            rows={6}
            value={content}
            required
            onChange={(event) => setContent(event.target.value)}
            placeholder="Paste any content. DeepMine will turn it into a capsule."
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-white">
          <input
            type="checkbox"
            checked={includeInRag}
            onChange={(event) => setIncludeInRag(event.target.checked)}
            className="rounded border-white/30 bg-transparent"
          />
          Include in RAG scope
        </label>
        <Button type="submit" disabled={pending}>
          {pending ? "Submitting..." : "Create Capsule"}
        </Button>
        {status && <p className="text-sm text-white/70">{status}</p>}
      </div>
    </form>
  );
}
