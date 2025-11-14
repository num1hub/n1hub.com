import { CapsuleDetail } from "@/components/capsule-detail";
import type { Capsule } from "@/lib/types";
import { engineRequest } from "@/lib/server-client";

interface Props {
  params: {
    id: string;
  };
}

export default async function CapsuleDetailPage({ params }: Props) {
  let capsule: Capsule | null = null;
  try {
    capsule = await engineRequest<Capsule>(`/capsules/${params.id}`);
  } catch (error) {
    console.error("Capsule fetch failed", error);
  }

  if (!capsule) {
    return (
      <main>
        <p className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 text-sm text-white/70">
          Capsule not found or the engine is offline.
        </p>
      </main>
    );
  }

  return (
    <main>
      <CapsuleDetail capsule={capsule} />
    </main>
  );
}
