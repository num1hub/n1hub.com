"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { Capsule } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { cn, truncate } from "@/lib/utils";
import { toggleCapsule } from "@/lib/api";

export function CapsuleCard({ capsule }: { capsule: Capsule }) {
  const queryClient = useQueryClient();
  const { mutateAsync, isPending } = useMutation({
    mutationFn: (include: boolean) => toggleCapsule(capsule.metadata.capsule_id, include),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["capsules"] });
    }
  });

  return (
    <div className="rounded-2xl border border-white/10 bg-gradient-to-b from-slate-900/70 to-slate-950/50 p-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/40">Capsule</p>
          <p className="text-lg font-semibold text-white">{capsule.metadata.capsule_id}</p>
        </div>
        <span
          className={cn(
            "rounded-full px-3 py-1 text-xs font-semibold",
            capsule.include_in_rag ? "bg-emerald-500/20 text-emerald-200" : "bg-white/10 text-white/70"
          )}
        >
          {capsule.include_in_rag ? "Included in RAG" : "RAG off"}
        </span>
      </div>
      <p className="mt-3 text-sm text-white/70">{truncate(capsule.neuro_concentrate.summary, 360)}</p>
      <div className="mt-4 flex flex-wrap gap-2 text-xs text-white/70">
        {capsule.metadata.tags.map((tag) => (
          <span key={tag} className="rounded-full bg-white/10 px-3 py-1">
            {tag}
          </span>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-white/60">
        <p>{capsule.metadata.language.toUpperCase()}</p>
        <p>hash: {capsule.metadata.semantic_hash}</p>
        <p>created {new Date(capsule.metadata.created_at).toLocaleDateString()}</p>
      </div>
      <div className="mt-5 flex items-center gap-3">
        <Button
          variant={capsule.include_in_rag ? "ghost" : "default"}
          disabled={isPending}
          onClick={() => mutateAsync(!capsule.include_in_rag)}
        >
          {capsule.include_in_rag ? "Disable in RAG" : "Enable in RAG"}
        </Button>
      </div>
    </div>
  );
}
