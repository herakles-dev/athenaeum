"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import SearchBar from "@/components/SearchBar";
import SearchResultCard from "@/components/SearchResultCard";
import TranscriptViewer from "@/components/TranscriptViewer";
import { api, type SearchResult } from "@/lib/api";

const DEFAULT_SUGGESTIONS = [
  "What is the ego?",
  "wu wei",
  "fear of death",
  "the present moment",
  "life as play",
  "Zen and silence",
  "Tao is water",
  "consciousness and dreams",
];

export default function SearchPage() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>(DEFAULT_SUGGESTIONS);

  useEffect(() => {
    api
      .info()
      .then((data) => {
        if (data.frontend.suggestions?.length > 0) {
          setSuggestions(data.frontend.suggestions);
        }
      })
      .catch(() => {
        // Keep default suggestions on error
      });
  }, []);

  async function handleSearch(q: string) {
    setQuery(q);
    setLoading(true);
    setSearched(true);
    setError(null);
    try {
      const data = await api.search(q, 20);
      setResults(data.results);
    } catch (e) {
      setResults([]);
      setError(e instanceof Error ? e.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {/* Hero */}
      <div className="text-center mb-10 pt-4">
        <h1
          className="text-4xl font-bold mb-3 tracking-tight"
          style={{ letterSpacing: "-0.02em" }}
        >
          Alan Watts Library
        </h1>
        <p className="text-base mb-1" style={{ color: "var(--muted)" }}>
          Semantic search across 238 lectures and essays
        </p>
        <div className="flex items-center justify-center gap-2 mt-3">
          {["1.7M words", "4,293 chunks", "15 topics"].map((s) => (
            <span key={s} className="badge">
              {s}
            </span>
          ))}
        </div>
        <div className="mt-5">
          <Link href="/chat" className="btn-glow">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            Chat with AI Alan Watts Librarian
          </Link>
        </div>
      </div>

      {/* Search */}
      <div className="max-w-2xl mx-auto mb-6">
        <SearchBar
          onSearch={handleSearch}
          loading={loading}
          placeholder="Search lectures… ego, wu wei, fear of death"
        />
      </div>

      {/* Suggestions (only before first search) */}
      {!searched && (
        <div className="max-w-2xl mx-auto mb-10">
          <p className="text-xs text-center mb-3" style={{ color: "var(--muted-2)" }}>
            Try a suggestion
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => handleSearch(s)}
                className="text-xs px-3 py-1.5 rounded-full transition-colors"
                style={{
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  color: "var(--muted)",
                }}
                onMouseEnter={(e) => {
                  (e.target as HTMLElement).style.borderColor =
                    "rgba(217,119,6,0.4)";
                  (e.target as HTMLElement).style.color = "var(--text)";
                }}
                onMouseLeave={(e) => {
                  (e.target as HTMLElement).style.borderColor = "var(--border)";
                  (e.target as HTMLElement).style.color = "var(--muted)";
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <p
          className="text-center text-sm mb-4"
          style={{ color: "#f87171" }}
        >
          {error}
        </p>
      )}

      {/* Empty state */}
      {searched && !loading && results.length === 0 && !error && (
        <p className="text-center text-sm" style={{ color: "var(--muted)" }}>
          No results for &ldquo;{query}&rdquo;
        </p>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="animate-in">
          <p className="text-xs mb-4" style={{ color: "var(--muted)" }}>
            {results.length} results for &ldquo;{query}&rdquo;
          </p>
          <div className="grid gap-3">
            {results.map((r) => (
              <SearchResultCard
                key={r.chunk_id}
                result={r}
                onClick={() => setSelectedId(r.transcript_id)}
              />
            ))}
          </div>
        </div>
      )}

      {selectedId !== null && (
        <TranscriptViewer
          transcriptId={selectedId}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  );
}
