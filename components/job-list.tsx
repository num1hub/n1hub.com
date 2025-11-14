"use client";

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { listJobs, cancelJob } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";
import { Button } from "@/components/ui/button";
import type { Job } from "@/lib/types";

function StateBadge({ state, code, stage }: { state: Job["state"]; code: number; stage: string }) {
  const palette: Record<Job["state"], string> = {
    pending: "bg-white/10 text-white",
    processing: "bg-blue-500/20 text-blue-200",
    succeeded: "bg-emerald-500/20 text-emerald-200",
    failed: "bg-red-500/20 text-red-200"
  };
  return (
    <div className="flex items-center gap-2">
      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${palette[state]}`}>{state}</span>
      <span className="text-xs text-white/50">{code} - {stage}</span>
    </div>
  );
}

export function JobList() {
  const queryClient = useQueryClient();
  const [sseConnected, setSseConnected] = useState(false);
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["jobs"],
    queryFn: listJobs,
    refetchInterval: sseConnected ? false : 5000, // Poll only if SSE not connected
  });

  useEffect(() => {
    // Try to connect to SSE
    const sseUrl = process.env.NEXT_PUBLIC_SSE_URL || "/api/events";
    const eventSource = new EventSource(`${sseUrl}/stream`);

    eventSource.onopen = () => {
      setSseConnected(true);
    };

    eventSource.onmessage = (event) => {
      if (event.data.startsWith("data: ")) {
        try {
          const update = JSON.parse(event.data.slice(6));
          // Update query cache with job update
          queryClient.setQueryData<Job[]>(["jobs"], (old) => {
            if (!old) return old;
            return old.map((job) =>
              job.id === update.job_id
                ? {
                    ...job,
                    code: update.code,
                    stage: update.stage,
                    state: update.state,
                    progress: update.progress,
                    capsule_id: update.capsule_id,
                  }
                : job
            );
          });
        } catch {
          // Ignore parse errors
        }
      }
    };

    eventSource.onerror = () => {
      setSseConnected(false);
      eventSource.close();
      // Fallback to polling
      refetch();
    };

    return () => {
      eventSource.close();
    };
  }, [queryClient, refetch]);

  if (isLoading) {
    return <p className="text-sm text-white/70">Loading jobs...</p>;
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Recent jobs</h2>
        <Button variant="ghost" onClick={() => refetch()} disabled={isFetching}>
          Refresh
        </Button>
      </div>
      <div className="space-y-3">
        {(data ?? []).map((job) => (
          <div key={job.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm text-white/80">Job #{job.id}</p>
                <p className="text-xs text-white/50">
                  {formatDistanceToNow(new Date(job.updated_at), { addSuffix: true })}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <StateBadge state={job.state} code={job.code} stage={job.stage} />
                {job.state === "processing" && job.code < 180 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={async () => {
                      try {
                        await cancelJob(job.id);
                        await queryClient.invalidateQueries({ queryKey: ["jobs"] });
                      } catch (error) {
                        console.error("Failed to cancel job:", error);
                      }
                    }}
                    className="text-xs"
                  >
                    Cancel
                  </Button>
                )}
              </div>
            </div>
            <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-white/10">
              <div className="h-full bg-brand" style={{ width: `${job.progress}%` }} />
            </div>
            {job.error && (
              <div className="mt-2 text-xs text-red-300">
                <p>Error {job.error.code} in {job.error.stage}:</p>
                <ul className="list-disc list-inside ml-2">
                  {job.error.issues?.map((issue, idx) => (
                    <li key={idx}>{issue.path}: {issue.message}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
        {data && data.length === 0 && (
          <p className="text-sm text-white/60">No jobs yet. Upload something to kick off DeepMine.</p>
        )}
      </div>
    </div>
  );
}
