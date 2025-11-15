"use client";

import { useMemo, useState } from "react";

import type { Capsule } from "@/lib/types";

type PositionedNode = {
  capsule: Capsule;
  x: number;
  y: number;
};

type PositionedLink = {
  source: PositionedNode;
  target: PositionedNode;
  rel: string;
};

const SVG_WIDTH = 520;
const SVG_HEIGHT = 360;
const NODE_RADIUS = 20;

export function GraphView({ capsules }: { capsules: Capsule[] }) {
  const [hoverId, setHoverId] = useState<string | null>(null);
  const nodes = useMemo<PositionedNode[]>(() => {
    const limitedNodes = capsules.slice(0, 12);

    if (limitedNodes.length === 0) {
      return [];
    }

    if (limitedNodes.length === 1) {
      return [
        {
          capsule: limitedNodes[0],
          x: SVG_WIDTH / 2,
          y: SVG_HEIGHT / 2,
        },
      ];
    }

    const radius = Math.min(SVG_WIDTH, SVG_HEIGHT) * 0.38;
    const centerX = SVG_WIDTH / 2;
    const centerY = SVG_HEIGHT / 2;

    return limitedNodes.map((capsule, index) => {
      const angle = (2 * Math.PI * index) / limitedNodes.length - Math.PI / 2;
      return {
        capsule,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    });
  }, [capsules]);

  const links = useMemo<PositionedLink[]>(() => {
    if (nodes.length === 0) {
      return [];
    }

    const nodeMap = new Map(nodes.map((node) => [node.capsule.metadata.capsule_id, node] as const));

    return nodes.flatMap((node) =>
      node.capsule.recursive.links
        .map((link) => {
          const targetNode = nodeMap.get(link.target_capsule_id);
          if (!targetNode) return null;
          return { source: node, target: targetNode, rel: link.rel };
        })
        .filter((link): link is PositionedLink => Boolean(link))
    );
  }, [nodes]);

  const hoveredNode = nodes.find((node) => node.capsule.metadata.capsule_id === hoverId);
  const relatedIds = useMemo(() => {
    if (!hoveredNode) return new Set<string>();
    const outgoing = links
      .filter((link) => link.source === hoveredNode || link.target === hoveredNode)
      .flatMap((link) => [link.source.capsule.metadata.capsule_id, link.target.capsule.metadata.capsule_id]);
    return new Set(outgoing);
  }, [hoveredNode, links]);

  return (
    <div className="min-h-[360px] rounded-2xl border border-white/10 bg-slate-900/60 p-4">
      <p className="text-sm font-semibold text-white">Graph (hop = 1)</p>
      <div className="mt-4 flex flex-col gap-4 md:flex-row">
        <div className="relative w-full overflow-hidden rounded-2xl border border-white/10 bg-black/20">
          <svg
            className="h-[280px] w-full"
            viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
            role="img"
            aria-label="Capsule knowledge graph"
          >
            <defs>
              <marker
                id="arrowhead"
                markerWidth="8"
                markerHeight="8"
                refX="6"
                refY="4"
                orient="auto"
                markerUnits="strokeWidth"
              >
                <path d="M 0 0 L 8 4 L 0 8 z" className="fill-white/40" />
              </marker>
            </defs>
            <rect width="100%" height="100%" rx="24" className="fill-transparent" />
            {links.map((link) => {
              const isActive = hoverId ? relatedIds.has(link.source.capsule.metadata.capsule_id) && relatedIds.has(link.target.capsule.metadata.capsule_id) : true;
              return (
                <g key={`${link.source.capsule.metadata.capsule_id}-${link.target.capsule.metadata.capsule_id}-${link.rel}`}>
                  <line
                    x1={link.source.x}
                    y1={link.source.y}
                    x2={link.target.x}
                    y2={link.target.y}
                    className={`stroke-white/30 transition-opacity ${isActive ? "opacity-100" : "opacity-20"}`}
                    strokeWidth={1.5}
                    markerEnd="url(#arrowhead)"
                  />
                  <text
                    x={(link.source.x + link.target.x) / 2}
                    y={(link.source.y + link.target.y) / 2 - 6}
                    className={`fill-white/60 text-[10px] ${isActive ? "opacity-100" : "opacity-20"}`}
                  >
                    {link.rel}
                  </text>
                </g>
              );
            })}
            {nodes.map((node) => {
              const id = node.capsule.metadata.capsule_id;
              const isHovered = hoverId === id;
              const isRelated = relatedIds.has(id);
              return (
                <g key={id}>
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={NODE_RADIUS}
                    className={`cursor-pointer transition-all duration-200 ${
                      isHovered
                        ? "fill-sky-400/90 stroke-white"
                        : isRelated
                          ? "fill-sky-400/40 stroke-white/80"
                          : "fill-white/15 stroke-white/40"
                    }`}
                    strokeWidth={2}
                    onMouseEnter={() => setHoverId(id)}
                    onMouseLeave={() => setHoverId(null)}
                  />
                  <text
                    x={node.x}
                    y={node.y + 3}
                    textAnchor="middle"
                    className="fill-white text-[10px] font-medium"
                  >
                    {id}
                  </text>
                </g>
              );
            })}
          </svg>
          {hoveredNode ? (
            <div className="pointer-events-none absolute inset-x-4 bottom-4 rounded-xl border border-white/10 bg-black/70 p-3 text-xs text-white/80">
              <p className="text-white">{hoveredNode.capsule.metadata.capsule_id}</p>
              {hoveredNode.capsule.metadata.title && (
                <p className="mt-1 line-clamp-2 text-white/70">{hoveredNode.capsule.metadata.title}</p>
              )}
              {hoveredNode.capsule.metadata.tags.length > 0 && (
                <p className="mt-1 text-[11px] uppercase tracking-wide text-white/40">
                  {hoveredNode.capsule.metadata.tags.join(" · ")}
                </p>
              )}
            </div>
          ) : (
            <div className="pointer-events-none absolute inset-x-4 bottom-4 rounded-xl border border-white/5 bg-black/60 p-3 text-xs text-white/60">
              Hover a node to inspect its capsule metadata.
            </div>
          )}
        </div>
        <div className="flex-1 space-y-3 text-xs text-white/70">
          <p className="font-medium text-white">Relations in view</p>
          {links.length === 0 ? (
            <p>No links yet. DeepMine will start building typed relations after more capsules.</p>
          ) : (
            <ul className="space-y-2">
              {links.map((link) => {
                const key = `${link.source.capsule.metadata.capsule_id}-${link.target.capsule.metadata.capsule_id}-${link.rel}`;
                return (
                  <li key={key} className="rounded-xl border border-white/5 bg-black/40 p-2">
                    <span className="text-white">{link.source.capsule.metadata.capsule_id}</span> {"→"} {link.rel} {"→"}{" "}
                    <span className="text-white">{link.target.capsule.metadata.capsule_id}</span>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
