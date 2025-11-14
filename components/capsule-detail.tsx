"use client";

import { Button } from "@/components/ui/button";
import type { Capsule } from "@/lib/types";

export function CapsuleDetail({ capsule }: { capsule: Capsule }) {
  const handleExportJson = () => {
    const json = JSON.stringify(capsule, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `capsule-${capsule.metadata.capsule_id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">{capsule.metadata.capsule_id}</h1>
        <Button onClick={handleExportJson} variant="ghost">
          Export JSON
        </Button>
      </div>
      <section className="rounded-2xl border border-white/10 bg-slate-900/60 p-5">
        <h2 className="text-lg font-semibold text-white">Metadata</h2>
        <div className="mt-3 grid gap-2 text-sm text-white/70 md:grid-cols-2">
          <div>ID: {capsule.metadata.capsule_id}</div>
          <div>Status: {capsule.metadata.status}</div>
          <div>Author: {capsule.metadata.author}</div>
          <div>Language: {capsule.metadata.language}</div>
          <div>Semantic hash: {capsule.metadata.semantic_hash}</div>
        </div>
      </section>
      <section className="rounded-2xl border border-white/10 bg-slate-900/60 p-5">
        <h2 className="text-lg font-semibold text-white">Core payload</h2>
        <pre className="mt-3 whitespace-pre-wrap text-sm text-white/80">{capsule.core_payload.content}</pre>
      </section>
      <section className="rounded-2xl border border-white/10 bg-slate-900/60 p-5">
        <h2 className="text-lg font-semibold text-white">Neuro concentrate</h2>
        <p className="text-sm text-white/80">{capsule.neuro_concentrate.summary}</p>
        <div className="mt-3 flex flex-wrap gap-2 text-xs text-white/70">
          {capsule.neuro_concentrate.keywords.map((keyword) => (
            <span key={keyword} className="rounded-full bg-white/10 px-3 py-1">
              {keyword}
            </span>
          ))}
        </div>
      </section>
      <section className="rounded-2xl border border-white/10 bg-slate-900/60 p-5">
        <h2 className="text-lg font-semibold text-white">Graph links</h2>
        <div className="mt-2 space-y-2 text-sm text-white/70">
          {capsule.recursive.links.map((link) => (
            <div key={`${link.rel}-${link.target_capsule_id}`} className="rounded-xl bg-black/30 px-3 py-2">
              <p>
                {link.rel} > {link.target_capsule_id} ({(link.confidence * 100).toFixed(0)}%)
              </p>
              <p className="text-xs text-white/50">{link.reason}</p>
            </div>
          ))}
          {capsule.recursive.links.length === 0 && <p>No links recorded.</p>}
        </div>
      </section>
    </div>
  );
}
