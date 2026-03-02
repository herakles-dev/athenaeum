"use client";

import { useState } from "react";
import TopicGrid from "@/components/TopicGrid";
import TopicDetail from "@/components/TopicDetail";

export default function TopicsPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Philosophical Topics</h1>
        <p className="text-sm mt-1" style={{ color: "var(--muted)" }}>
          15 themes auto-discovered via K-Means clustering on 4,293 embedded chunks.
        </p>
      </div>
      {selectedId !== null ? (
        <TopicDetail topicId={selectedId} onClose={() => setSelectedId(null)} />
      ) : (
        <TopicGrid onSelect={setSelectedId} />
      )}
    </div>
  );
}
