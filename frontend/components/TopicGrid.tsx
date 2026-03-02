"use client";

import { useEffect, useState } from "react";
import { api, type TopicSummary } from "@/lib/api";

interface Props {
  onSelect: (id: number) => void;
}

// Skeleton card
function TopicSkeleton() {
  return (
    <div className="card p-5">
      <div className="skeleton h-4 w-3/4 mb-2" />
      <div className="skeleton h-3 w-1/3 mb-4" />
      <div className="flex gap-1.5">
        <div className="skeleton h-5 w-14 rounded-full" />
        <div className="skeleton h-5 w-16 rounded-full" />
        <div className="skeleton h-5 w-12 rounded-full" />
      </div>
    </div>
  );
}

export default function TopicGrid({ onSelect }: Props) {
  const [topics, setTopics] = useState<TopicSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .topics()
      .then(setTopics)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <TopicSkeleton key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {topics.map((t) => (
        <button
          key={t.id}
          onClick={() => onSelect(t.id)}
          className="card-hover text-left p-5"
        >
          <h3 className="font-semibold text-sm leading-snug mb-1.5">
            {t.name}
          </h3>
          <p className="text-xs mb-3.5" style={{ color: "var(--muted)" }}>
            {t.transcript_count} lectures &middot; {t.chunk_count} passages
          </p>
          <div className="flex flex-wrap gap-1.5">
            {t.keywords.slice(0, 6).map((kw) => (
              <span key={kw} className="badge">
                {kw}
              </span>
            ))}
          </div>
        </button>
      ))}
    </div>
  );
}
