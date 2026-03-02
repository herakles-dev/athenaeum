"use client";

import { useState } from "react";
import TranscriptList from "@/components/TranscriptList";
import TranscriptViewer from "@/components/TranscriptViewer";

export default function BrowsePage() {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Browse Transcripts</h1>
        <p className="text-sm mt-1" style={{ color: "var(--muted)" }}>
          238 lectures and essays — filter by series or search by keyword.
        </p>
      </div>
      <TranscriptList onSelect={setSelectedId} />
      {selectedId !== null && (
        <TranscriptViewer transcriptId={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </div>
  );
}
