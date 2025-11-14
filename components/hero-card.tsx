"use client";

import { motion } from "framer-motion";
import Link from "next/link";

export function HeroCard() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="rounded-3xl border border-white/10 bg-gradient-to-br from-brand/20 via-slate-900 to-slate-950 p-6 shadow-card"
    >
      <p className="text-xs uppercase tracking-[0.3em] text-white/60">N1Hub pipeline</p>
      <h1 className="mt-3 text-3xl font-semibold text-white">Anything -> Capsules -> Graph -> Chat</h1>
      <p className="mt-4 text-sm text-white/70">
        Drop material, watch jobs run through the 9-step DeepMine pipeline, explore structured capsules, and chat with grounded RAG scopes.
        Everything here is wired to the approved N1Hub v0.1 capsule spec.
      </p>
      <div className="mt-6 flex flex-col gap-2 text-sm text-white/70">
        <p>- Inbox tracks ingestion jobs (INGEST -> REPORT)</p>
        <p>- Capsules expose the 4-section CapsuleOS contract</p>
        <p>- Graph shows typed links with hop=1 preview</p>
        <p>- Chat enforces citations + RAG-Scope filters</p>
      </div>
      <div className="mt-6 flex gap-3">
        <Link href="/chat" className="rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900">
          Go to chat
        </Link>
        <Link href="/capsules" className="rounded-full bg-white/10 px-4 py-2 text-sm text-white">
          Review capsules
        </Link>
      </div>
    </motion.section>
  );
}
