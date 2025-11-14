import { GraphView } from "@/components/graph-view";
import type { Capsule } from "@/lib/types";
import { engineRequest } from "@/lib/server-client";

export default async function GraphPage() {
  let capsules: Capsule[] = [];
  try {
    capsules = await engineRequest<Capsule[]>("/capsules");
  } catch (error) {
    console.error("Graph data failed", error);
  }
  return (
    <main>
      <GraphView capsules={capsules} />
    </main>
  );
}
