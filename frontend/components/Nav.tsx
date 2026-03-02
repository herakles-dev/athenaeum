"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const navLinks = [
  { href: "/", label: "Search" },
  { href: "/chat", label: "Chat" },
  { href: "/browse", label: "Browse" },
  { href: "/topics", label: "Topics" },
];

export default function Nav() {
  const path = usePathname();
  const [corpusStats, setCorpusStats] = useState<string | null>(null);

  useEffect(() => {
    api
      .info()
      .then((data) => {
        const { transcript_count, chunk_count } = data.corpus;
        setCorpusStats(
          `${transcript_count.toLocaleString()} lectures · ${chunk_count.toLocaleString()} chunks`
        );
      })
      .catch(() => {
        // Fallback: show nothing rather than stale hardcoded data
      });
  }, []);

  const isActive = (href: string) =>
    href === "/" ? path === "/" : path.startsWith(href);

  return (
    <header
      className="border-b px-6 flex items-center gap-0 h-14"
      style={{
        borderColor: "var(--border)",
        background: "var(--surface)",
        position: "sticky",
        top: 0,
        zIndex: 40,
        backdropFilter: "blur(8px)",
      }}
    >
      {/* Brand */}
      <Link
        href="/"
        className="font-semibold text-base tracking-tight mr-8 shrink-0"
        style={{ color: "var(--accent)" }}
      >
        Alan Watts
      </Link>

      {/* Nav links */}
      <nav className="flex items-stretch h-full text-sm gap-1">
        {navLinks.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className="flex items-center px-3 h-full relative transition-colors"
            style={{
              color: isActive(l.href) ? "var(--text)" : "var(--muted)",
            }}
          >
            {l.label}
            {isActive(l.href) && (
              <span
                className="absolute bottom-0 left-0 right-0 h-0.5 rounded-t"
                style={{ background: "var(--accent)" }}
              />
            )}
          </Link>
        ))}
      </nav>

      {/* Right side */}
      <div className="ml-auto flex items-center gap-3">
        <span
          className="text-xs hidden sm:block"
          style={{
            color: "var(--muted-2)",
            minWidth: "12ch",
            transition: "opacity 0.3s",
            opacity: corpusStats ? 1 : 0,
          }}
        >
          {corpusStats}
        </span>
        <Link
          href="/settings"
          className="flex items-center justify-center w-8 h-8 rounded-lg transition-colors"
          style={{
            color: isActive("/settings") ? "var(--accent)" : "var(--muted)",
            background: isActive("/settings") ? "var(--accent-dim)" : "transparent",
            border: "1px solid",
            borderColor: isActive("/settings") ? "rgba(217,119,6,0.2)" : "var(--border)",
          }}
          title="Settings"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
          </svg>
        </Link>
      </div>
    </header>
  );
}
