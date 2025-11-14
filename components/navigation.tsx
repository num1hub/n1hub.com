"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Home" },
  { href: "/inbox", label: "Inbox" },
  { href: "/capsules", label: "My Capsules" },
  { href: "/graph", label: "Graph" },
  { href: "/chat", label: "Chat" }
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <header className="rounded-2xl border border-white/10 bg-slate-900/40 px-4 py-3 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/60">N1Hub v0.1</p>
          <p className="font-semibold text-white">Anything > Capsules > Graph > Chat</p>
        </div>
        <nav className="flex flex-wrap gap-2 text-sm">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-full px-3 py-1 text-white/70 transition",
                pathname === link.href ? "bg-brand/20 text-white" : "hover:bg-white/10"
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
