"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listCapsules } from "@/lib/api";
import { CapsuleCard } from "@/components/capsule-card";

export function CapsulesView() {
  const [onlyIncluded, setOnlyIncluded] = useState(false);
  const { data, isLoading } = useQuery({
    queryKey: ["capsules"],
    queryFn: () => listCapsules()
  });

  const capsules = useMemo(() => {
    if (!data) {
      return [];
    }
    return data.filter((capsule) => (onlyIncluded ? capsule.include_in_rag : true));
  }, [data, onlyIncluded]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">My Capsules</h2>
        <label className="flex items-center gap-2 text-sm text-white/70">
          <input
            type="checkbox"
            checked={onlyIncluded}
            onChange={(event) => setOnlyIncluded(event.target.checked)}
            className="rounded"
          />
          RAG only
        </label>
      </div>
      {isLoading && <p className="text-sm text-white/70">Loading capsules�</p>}
      <div className="grid gap-4">
        {capsules.map((capsule) => (
          <CapsuleCard key={capsule.metadata.capsule_id} capsule={capsule} />
        ))}
      </div>
      {!isLoading && capsules.length === 0 && (
        <p className="text-sm text-white/60">No capsules yet. Upload in the Inbox to start.</p>
      )}
    </div>
  );
}
