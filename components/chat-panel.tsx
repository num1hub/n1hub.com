"use client";

import { useState } from "react";
import { runChat } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useRagScope } from "@/lib/state";

interface Message {
  role: "user" | "assistant";
  text: string;
  sources?: string[];
  metrics?: Record<string, number>;
}

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const { getScopeForAPI } = useRagScope();

  async function handleSend() {
    if (!input.trim()) {
      return;
    }
    const question = input.trim();
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setIsSending(true);
    try {
      const response = await runChat({ query: question, scope: getScopeForAPI() });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: response.answer,
          sources: response.sources,
          metrics: response.metrics
        }
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: `Chat error: ${(error as Error).message}`
        }
      ]);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
        <Textarea
          value={input}
          rows={4}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask grounded questions about your capsules"
        />
        <div className="mt-3 flex items-center justify-between text-xs text-white/50">
          <p>Scope: {getScopeForAPI().join(", ") || "my (default)"}</p>
          <Button onClick={handleSend} disabled={isSending}>Ask</Button>
        </div>
      </div>
      <div className="space-y-3">
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className="rounded-2xl border border-white/5 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">{message.role}</p>
            <p className="mt-2 whitespace-pre-line text-sm text-white">{message.text}</p>
            {message.sources && message.sources.length > 0 && (
              <div className="mt-2 text-xs text-white/60">
                Sources: {message.sources.join(", ")}
              </div>
            )}
            {message.metrics && (
              <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-white/60">
                {Object.entries(message.metrics).map(([key, value]) => (
                  <div key={key} className="rounded-xl bg-black/30 px-2 py-1">
                    {key}: {(value * 100).toFixed(1)}%
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {messages.length === 0 && <p className="text-sm text-white/60">No chat messages yet. Ask something about a capsule.</p>}
      </div>
    </div>
  );
}
