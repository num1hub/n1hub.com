import type { Capsule } from "@/lib/types";

export function GraphView({ capsules }: { capsules: Capsule[] }) {
  const nodes = capsules.slice(0, 12);
  const links = nodes.flatMap((capsule) =>
    capsule.recursive.links
      .filter((link) => nodes.some((node) => node.metadata.capsule_id === link.target_capsule_id))
      .map((link) => ({ source: capsule.metadata.capsule_id, target: link.target_capsule_id, rel: link.rel }))
  );

  return (
    <div className="min-h-[360px] rounded-2xl border border-white/10 bg-slate-900/60 p-4">
      <p className="text-sm font-semibold text-white">Graph (hop = 1)</p>
      <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-3">
        {nodes.map((capsule) => (
          <div key={capsule.metadata.capsule_id} className="rounded-2xl border border-white/10 bg-black/30 p-3 text-xs">
            <p className="font-semibold text-white">{capsule.metadata.capsule_id}</p>
            <p className="mt-1 text-white/60">{capsule.metadata.tags.join(", ")}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 space-y-2 text-xs text-white/70">
        {links.length === 0 && <p>No links yet. DeepMine will start building typed relations after more capsules.</p>}
        {links.map((link) => (
          <p key={`${link.source}-${link.target}-${link.rel}`}>
            <span className="text-white">{link.source}</span> {">"} {link.rel} {">"} <span className="text-white">{link.target}</span>
          </p>
        ))}
      </div>
    </div>
  );
}
