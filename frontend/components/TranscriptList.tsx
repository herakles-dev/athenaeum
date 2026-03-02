"use client";

import { useState, useEffect } from "react";
import { api, type TranscriptSummary, type SeriesInfo } from "@/lib/api";

interface Props {
  onSelect: (id: number) => void;
}

function TranscriptSkeleton() {
  return (
    <li className="card px-4 py-3">
      <div className="skeleton h-4 w-2/3 mb-2" />
      <div className="skeleton h-3 w-1/3" />
    </li>
  );
}

export default function TranscriptList({ onSelect }: Props) {
  const [transcripts, setTranscripts] = useState<TranscriptSummary[]>([]);
  const [series, setSeries] = useState<SeriesInfo[]>([]);
  const [selectedSeries, setSelectedSeries] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.series().then(setSeries).catch(console.error);
  }, []);

  useEffect(() => {
    setLoading(true);
    api
      .transcripts({
        series: selectedSeries ?? undefined,
        search: search || undefined,
        limit: 200,
      })
      .then(setTranscripts)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedSeries, search]);

  return (
    <div className="flex gap-6">
      {/* Series sidebar */}
      <aside className="w-44 shrink-0">
        <p className="section-label mb-3">Series</p>
        <ul className="space-y-0.5 text-sm">
          <li>
            <button
              onClick={() => setSelectedSeries(null)}
              className="w-full text-left px-2.5 py-1.5 rounded-lg text-sm transition-colors"
              style={{
                color: !selectedSeries ? "var(--accent)" : "var(--muted)",
                background: !selectedSeries ? "var(--accent-dim)" : "transparent",
              }}
            >
              All series
            </button>
          </li>
          {series.map((s) => (
            <li key={s.series}>
              <button
                onClick={() => setSelectedSeries(s.series)}
                className="w-full text-left px-2.5 py-1.5 rounded-lg text-sm transition-colors"
                style={{
                  color:
                    selectedSeries === s.series
                      ? "var(--accent)"
                      : "var(--muted)",
                  background:
                    selectedSeries === s.series
                      ? "var(--accent-dim)"
                      : "transparent",
                }}
                onMouseEnter={(e) => {
                  if (selectedSeries !== s.series)
                    (e.currentTarget as HTMLElement).style.color = "var(--text)";
                }}
                onMouseLeave={(e) => {
                  if (selectedSeries !== s.series)
                    (e.currentTarget as HTMLElement).style.color = "var(--muted)";
                }}
              >
                {s.series}
                <span
                  className="ml-1 text-xs"
                  style={{ color: "var(--muted-2)" }}
                >
                  ({s.count})
                </span>
              </button>
            </li>
          ))}
        </ul>
      </aside>

      {/* Main list */}
      <div className="flex-1 min-w-0">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter by title or keyword…"
          className="input mb-4"
        />

        {loading ? (
          <ul className="space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <TranscriptSkeleton key={i} />
            ))}
          </ul>
        ) : transcripts.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--muted)" }}>
            No transcripts found.
          </p>
        ) : (
          <>
            <p className="text-xs mb-3" style={{ color: "var(--muted-2)" }}>
              {transcripts.length} transcript{transcripts.length !== 1 ? "s" : ""}
            </p>
            <ul className="space-y-1.5">
              {transcripts.map((t) => (
                <li key={t.id}>
                  <button
                    onClick={() => onSelect(t.id)}
                    className="card-hover w-full text-left px-4 py-3"
                  >
                    <p className="text-sm font-medium leading-snug">
                      {t.title}
                    </p>
                    <p className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>
                      {t.series && `${t.series} · `}
                      {t.word_count.toLocaleString()} words
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}
