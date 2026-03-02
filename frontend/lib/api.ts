import { loadSettings } from "./settings";

// Use relative URL so the browser calls /api/* on the same origin (nginx routes it to the backend).
// NEXT_PUBLIC_API_URL can override for local dev pointing at a separate host.
const API_URL =
  (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

// ── Types ─────────────────────────────────────────────────────────────────────

export interface SearchResult {
  chunk_id: number;
  transcript_id: number;
  transcript_title: string;
  series: string | null;
  text: string;
  similarity: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

export interface ChatSource {
  title: string;
  series: string | null;
  similarity: number;
}

export interface ChatResponse {
  response: string;
  sources: ChatSource[];
}

export interface TranscriptSummary {
  id: number;
  title: string;
  series: string | null;
  source: string;
  word_count: number;
}

export interface TranscriptDetail extends TranscriptSummary {
  full_text: string;
  source_url: string | null;
  video_url: string | null;
}

export interface SeriesInfo {
  series: string;
  count: number;
}

export interface TopicSummary {
  id: number;
  name: string;
  chunk_count: number;
  transcript_count: number;
  keywords: string[];
}

export interface TopicDetail extends TopicSummary {
  transcripts: TranscriptSummary[];
}

export interface LibraryInfo {
  library: {
    name: string;
    title: string;
    author: string;
    domain: string;
    description: string;
  };
  corpus: {
    transcript_count: number;
    chunk_count: number;
    topic_count: number;
    series_count: number;
  };
  frontend: {
    suggestions: string[];
    heroTagline: string;
    accentColor: string;
  };
}

export interface ServerSettings {
  provider: string;
  model: string;
  has_api_key: boolean;
  base_url: string | null;
}

// ── API client ────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    let detail = body;
    try {
      const parsed = JSON.parse(body);
      detail = parsed.detail ?? body;
    } catch {}
    throw new Error(detail || `API error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  search: (q: string, limit = 10): Promise<SearchResponse> =>
    apiFetch(`/api/search?q=${encodeURIComponent(q)}&limit=${limit}`),

  chat: (message: string, contextLimit = 10): Promise<ChatResponse> => {
    const s = loadSettings();
    return apiFetch("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        message,
        context_limit: contextLimit,
        ...(s
          ? {
              llm_provider: s.provider,
              llm_model: s.model || undefined,
              llm_api_key: s.apiKey || undefined,
              llm_base_url: s.baseUrl || undefined,
            }
          : {}),
      }),
    });
  },

  transcripts: (params?: {
    series?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<TranscriptSummary[]> => {
    const qs = new URLSearchParams();
    if (params?.series) qs.set("series", params.series);
    if (params?.search) qs.set("search", params.search);
    if (params?.limit !== undefined) qs.set("limit", String(params.limit));
    if (params?.offset !== undefined) qs.set("offset", String(params.offset));
    return apiFetch(`/api/transcripts?${qs}`);
  },

  transcript: (id: number): Promise<TranscriptDetail> =>
    apiFetch(`/api/transcripts/${id}`),

  series: (): Promise<SeriesInfo[]> => apiFetch("/api/series"),

  topics: (): Promise<TopicSummary[]> => apiFetch("/api/topics"),

  topic: (id: number): Promise<TopicDetail> => apiFetch(`/api/topics/${id}`),

  info: (): Promise<LibraryInfo> => apiFetch("/api/info"),

  serverSettings: (): Promise<ServerSettings> => apiFetch("/api/settings"),

  testConnection: (payload: {
    provider: string;
    model?: string;
    api_key?: string;
    base_url?: string;
  }): Promise<{ ok: boolean; response?: string }> =>
    apiFetch("/api/settings/test", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
