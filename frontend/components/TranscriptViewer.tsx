"use client";

import { useEffect, useState, useCallback } from "react";
import { api, type TranscriptDetail } from "@/lib/api";

interface Props {
  transcriptId: number;
  onClose: () => void;
}

export default function TranscriptViewer({ transcriptId, onClose }: Props) {
  const [transcript, setTranscript] = useState<TranscriptDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setTranscript(null);
    api
      .transcript(transcriptId)
      .then(setTranscript)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [transcriptId]);

  const handleBackdrop = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget) onClose();
    },
    [onClose]
  );

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-8 px-4 pb-4"
      style={{ background: "rgba(0,0,0,0.75)", backdropFilter: "blur(4px)" }}
      onClick={handleBackdrop}
    >
      <div
        className="relative z-10 w-full max-w-3xl max-h-[90vh] rounded-2xl border flex flex-col modal-in"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="flex items-start justify-between gap-4 px-6 py-5 border-b shrink-0"
          style={{ borderColor: "var(--border)" }}
        >
          {loading ? (
            <div className="flex-1">
              <div className="skeleton h-5 w-64 mb-2" />
              <div className="skeleton h-3 w-40" />
            </div>
          ) : transcript ? (
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold leading-snug">
                {transcript.title}
              </h2>
              <div
                className="flex items-center gap-2 mt-1.5 flex-wrap"
                style={{ color: "var(--muted)" }}
              >
                {transcript.series && (
                  <span className="text-sm">{transcript.series}</span>
                )}
                {transcript.series && (
                  <span style={{ color: "var(--border)" }}>·</span>
                )}
                <span className="text-xs">{transcript.source}</span>
                {transcript.word_count && (
                  <>
                    <span style={{ color: "var(--border)" }}>·</span>
                    <span className="text-xs">
                      {transcript.word_count.toLocaleString()} words
                    </span>
                  </>
                )}
                {transcript.source_url && (
                  <>
                    <span style={{ color: "var(--border)" }}>·</span>
                    <a
                      href={transcript.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs underline hover:opacity-80"
                      style={{ color: "var(--accent)" }}
                    >
                      source ↗
                    </a>
                  </>
                )}
              </div>
            </div>
          ) : (
            <p style={{ color: "var(--muted)" }}>Transcript not found.</p>
          )}
          <button
            onClick={onClose}
            className="shrink-0 w-8 h-8 flex items-center justify-center rounded-lg transition-colors"
            style={{
              color: "var(--muted)",
              border: "1px solid var(--border)",
              background: "transparent",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.color = "var(--text)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.color = "var(--muted)";
            }}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Body */}
        {transcript && (
          <div className="overflow-y-auto px-6 py-5 prose-watts flex-1">
            {transcript.full_text.split("\n\n").map((para, i) =>
              para.trim() ? (
                <p key={i}>{para.trim()}</p>
              ) : null
            )}
          </div>
        )}

        {/* Footer */}
        <div
          className="px-6 py-3 border-t shrink-0 flex justify-end"
          style={{ borderColor: "var(--border)" }}
        >
          <button
            onClick={onClose}
            className="btn btn-ghost text-xs px-3 py-1.5 h-auto"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
