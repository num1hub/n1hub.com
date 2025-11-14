import { ChatPanel } from "@/components/chat-panel";
import { RagScopeToggle } from "@/components/rag-scope-toggle";
import { engineRequest } from "@/lib/server-client";
import type { Capsule } from "@/lib/types";

export default async function ChatPage() {
  let tags: string[] = [];
  try {
    const capsules = await engineRequest<Capsule[]>("/capsules");
    tags = Array.from(new Set(capsules.flatMap((capsule) => capsule.metadata.tags))).slice(0, 16);
  } catch (error) {
    console.error("Chat scope load failed", error);
  }

  return (
    <main className="space-y-6">
      <RagScopeToggle availableTags={tags} />
      <ChatPanel />
    </main>
  );
}
