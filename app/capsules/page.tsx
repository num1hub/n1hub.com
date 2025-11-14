import { CapsulesView } from "@/components/capsules-view";
import { RagScopeToggle } from "@/components/rag-scope-toggle";
import type { Capsule } from "@/lib/types";
import { engineRequest } from "@/lib/server-client";

export default async function CapsulesPage() {
  let tags: string[] = [];
  try {
    const capsules = await engineRequest<Capsule[]>("/capsules");
    tags = Array.from(new Set(capsules.flatMap((capsule) => capsule.metadata.tags))).slice(0, 16);
  } catch (error) {
    console.error("Failed to load capsule tags", error);
  }

  return (
    <main className="space-y-6">
      <RagScopeToggle availableTags={tags} />
      <CapsulesView />
    </main>
  );
}
