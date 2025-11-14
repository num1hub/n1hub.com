"use client";

import { useRagScope } from "@/lib/state";
import { Button } from "@/components/ui/button";

const SCOPE_TYPES = [
  { value: "my" as const, label: "My Capsules", description: "Your active capsules" },
  { value: "public" as const, label: "All Public", description: "Public capsules" },
  { value: "inbox" as const, label: "Collection: Inbox", description: "Last 30 days" },
  { value: "tags" as const, label: "Tags", description: "Filter by tags" },
] as const;

export function RagScopeToggle({ availableTags }: { availableTags: string[] }) {
  const { scopeType, scope, setScopeType, toggleTag } = useRagScope();

  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-white">RAG-Scope</p>
          <p className="text-xs text-white/50">Select scope profile for retrieval (Section 10).</p>
        </div>
        <Button variant="ghost" onClick={() => setScopeType("my")}>
          Reset
        </Button>
      </div>
      
      {/* Scope Type Selector */}
      <div className="mt-3 flex flex-wrap gap-2">
        {SCOPE_TYPES.map((type) => {
          const active = scopeType === type.value;
          return (
            <button
              key={type.value}
              onClick={() => setScopeType(type.value)}
              className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                active ? "bg-brand text-white" : "bg-white/10 text-white/70 hover:bg-white/20"
              }`}
              title={type.description}
            >
              {type.label}
            </button>
          );
        })}
      </div>

      {/* Tag Selection (only shown when scopeType is "tags") */}
      {scopeType === "tags" && (
        <div className="mt-3 flex flex-wrap gap-2">
          {availableTags.map((tag) => {
            const active = scope.includes(tag);
            return (
              <button
                key={tag}
                onClick={() => toggleTag(tag)}
                className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                  active ? "bg-brand/80 text-white" : "bg-white/10 text-white/70 hover:bg-white/20"
                }`}
              >
                {tag}
              </button>
            );
          })}
          {availableTags.length === 0 && (
            <p className="text-xs text-white/50">No tags yet. Ingest capsules to unlock tag filtering.</p>
          )}
        </div>
      )}
    </div>
  );
}
