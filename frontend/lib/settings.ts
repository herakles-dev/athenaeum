export interface LLMSettings {
  provider: "anthropic" | "openai" | "ollama" | "gemini" | "openrouter";
  model: string;
  apiKey: string;
  baseUrl: string;
}

const KEY = "aw_llm_settings";

const DEFAULTS: Record<LLMSettings["provider"], Partial<LLMSettings>> = {
  anthropic: { model: "claude-sonnet-4-6", baseUrl: "" },
  openai: { model: "gpt-4o", baseUrl: "" },
  ollama: { model: "llama3.2", baseUrl: "http://localhost:11434" },
  gemini: { model: "gemini-2.0-flash", baseUrl: "" },
  openrouter: { model: "", baseUrl: "" },
};

export function loadSettings(): LLMSettings | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as LLMSettings) : null;
  } catch {
    return null;
  }
}

export function saveSettings(s: LLMSettings): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(KEY, JSON.stringify(s));
}

export function clearSettings(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(KEY);
}

export function defaultsForProvider(
  provider: LLMSettings["provider"]
): Partial<LLMSettings> {
  return DEFAULTS[provider] ?? {};
}

export function hasSettings(): boolean {
  return loadSettings() !== null;
}
