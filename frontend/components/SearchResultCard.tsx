import type { SearchResult } from "@/lib/api";

interface Props {
  result: SearchResult;
  onClick?: () => void;
}

export default function SearchResultCard({ result, onClick }: Props) {
  const pct = Math.round(result.similarity * 100);
  const isStrong = pct >= 65;

  return (
    <div className="card-hover p-5" onClick={onClick}>
      <div className="flex items-start gap-4">
        {/* Similarity bar */}
        <div className="shrink-0 flex flex-col items-center gap-1 pt-0.5">
          <span
            className="text-xs font-mono font-semibold"
            style={{ color: isStrong ? "var(--accent)" : "var(--muted)" }}
          >
            {pct}%
          </span>
          <div
            className="w-0.5 rounded-full"
            style={{
              height: "2.5rem",
              background: isStrong
                ? `linear-gradient(to bottom, var(--accent), transparent)`
                : "var(--border)",
            }}
          />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3 mb-2">
            <div>
              <p className="font-medium text-sm leading-snug">
                {result.transcript_title}
              </p>
              {result.series && (
                <p className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>
                  {result.series}
                </p>
              )}
            </div>
            <span
              className="shrink-0 text-xs px-2 py-0.5 rounded mt-0.5"
              style={{
                background: "var(--surface-2)",
                color: "var(--muted)",
                border: "1px solid var(--border)",
                fontFamily: "monospace",
              }}
            >
              View →
            </span>
          </div>
          <p
            className="text-sm leading-relaxed line-clamp-4"
            style={{ color: "var(--muted)" }}
          >
            &ldquo;{result.text}&rdquo;
          </p>
        </div>
      </div>
    </div>
  );
}
