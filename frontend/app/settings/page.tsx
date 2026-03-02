"use client";

import { useState, useEffect } from "react";
import { api, type ServerSettings } from "@/lib/api";
import {
  loadSettings,
  saveSettings,
  clearSettings,
  defaultsForProvider,
  type LLMSettings,
} from "@/lib/settings";

type Provider = LLMSettings["provider"];
type TestState = "idle" | "testing" | "ok" | "error";

const PROVIDERS: { value: Provider; label: string; desc: string }[] = [
  { value: "openrouter", label: "OpenRouter", desc: "Free model fallback chain" },
  { value: "gemini", label: "Google Gemini", desc: "Gemini Flash / Pro" },
  { value: "anthropic", label: "Anthropic", desc: "Claude models" },
  { value: "openai", label: "OpenAI / Compatible", desc: "GPT-4, local endpoints" },
  { value: "ollama", label: "Ollama", desc: "Local open-source models" },
];

const OPENROUTER_FREE_MODELS = [
  "meta-llama/llama-3.3-70b-instruct:free",
  "stepfun/step-3.5-flash:free",
  "upstage/solar-pro-3:free",
  "z-ai/glm-4.5-air:free",
  "qwen/qwen3-next-80b-a3b-instruct:free",
  "mistralai/mistral-small-3.1-24b-instruct:free",
  "google/gemma-3-27b-it:free",
  "nousresearch/hermes-3-llama-3.1-405b:free",
  "google/gemma-3-12b-it:free",
  "meta-llama/llama-3.2-3b-instruct:free",
];

export default function SettingsPage() {
  const [serverCfg, setServerCfg] = useState<ServerSettings | null>(null);
  const [provider, setProvider] = useState<Provider>("anthropic");
  const [model, setModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [testState, setTestState] = useState<TestState>("idle");
  const [testMsg, setTestMsg] = useState("");
  const [saved, setSaved] = useState(false);
  const [usingServer, setUsingServer] = useState(false);

  useEffect(() => {
    api.serverSettings().then(setServerCfg).catch(() => null);
    const s = loadSettings();
    if (s) {
      setProvider(s.provider);
      setModel(s.model);
      setApiKey(s.apiKey);
      setBaseUrl(s.baseUrl);
    }
  }, []);

  function handleProviderChange(p: Provider) {
    setProvider(p);
    const d = defaultsForProvider(p);
    setModel(d.model ?? "");
    setBaseUrl(d.baseUrl ?? "");
    setTestState("idle");
    setTestMsg("");
  }

  async function handleTest() {
    setTestState("testing");
    setTestMsg("");
    try {
      const res = await api.testConnection({
        provider,
        model: model || undefined,
        api_key: apiKey || undefined,
        base_url: baseUrl || undefined,
      });
      setTestState("ok");
      setTestMsg(res.response ?? "Connected!");
    } catch (e: unknown) {
      setTestState("error");
      setTestMsg(e instanceof Error ? e.message : "Connection failed");
    }
  }

  function handleSave() {
    saveSettings({ provider, model, apiKey, baseUrl });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  function handleUseServer() {
    clearSettings();
    setApiKey("");
    setUsingServer(true);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  const needsApiKey = provider === "anthropic" || provider === "openai" || provider === "gemini" || provider === "openrouter";
  const needsBaseUrl = provider === "openai" || provider === "ollama";

  return (
    <div className="max-w-xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-1">Settings</h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Configure the LLM used for chat. Settings are saved in your browser.
        </p>
      </div>

      {/* Server default info */}
      {serverCfg && (
        <div
          className="rounded-lg p-4 mb-6 text-sm"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
          }}
        >
          <p className="section-label mb-2">Server Default</p>
          <div className="flex items-center justify-between">
            <div style={{ color: "var(--muted)" }}>
              <span
                className="font-medium"
                style={{ color: "var(--text)" }}
              >
                {serverCfg.provider}
              </span>
              {" / "}
              <span>{serverCfg.model || "default"}</span>
              {" · "}
              <span>
                {serverCfg.has_api_key ? "API key configured" : "No API key"}
              </span>
            </div>
            <button
              className="btn btn-ghost text-xs px-3 py-1.5 h-auto"
              onClick={handleUseServer}
            >
              Use server default
            </button>
          </div>
        </div>
      )}

      {/* Provider selection */}
      <section className="mb-5">
        <label className="section-label block mb-3">LLM Provider</label>
        <div className="grid grid-cols-2 gap-2">
          {PROVIDERS.map((p) => (
            <button
              key={p.value}
              onClick={() => handleProviderChange(p.value)}
              className="text-left rounded-lg p-3 transition-colors"
              style={{
                background:
                  provider === p.value ? "var(--accent-dim)" : "var(--surface)",
                border: `1px solid ${
                  provider === p.value
                    ? "rgba(217,119,6,0.3)"
                    : "var(--border)"
                }`,
              }}
            >
              <p
                className="text-sm font-medium"
                style={{
                  color:
                    provider === p.value ? "var(--accent)" : "var(--text)",
                }}
              >
                {p.label}
              </p>
              <p
                className="text-xs mt-0.5"
                style={{ color: "var(--muted)" }}
              >
                {p.desc}
              </p>
            </button>
          ))}
        </div>
      </section>

      {/* OpenRouter fallback chain info */}
      {provider === "openrouter" && (
        <div
          className="rounded-lg p-4 mb-5 text-sm"
          style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
        >
          <p className="section-label mb-2">Free Model Fallback Chain</p>
          <p className="text-xs mb-3" style={{ color: "var(--muted)" }}>
            Tries each model in order. Falls back automatically on errors or rate limits.
            Leave Model blank to use the full chain.
          </p>
          <ol className="space-y-1">
            {OPENROUTER_FREE_MODELS.map((m, i) => (
              <li key={m} className="flex items-center gap-2 text-xs" style={{ color: i === 0 ? "var(--accent)" : "var(--muted)" }}>
                <span
                  className="w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
                  style={{ background: i === 0 ? "var(--accent-dim)" : "var(--surface-2)", color: i === 0 ? "var(--accent)" : "var(--muted-2)" }}
                >
                  {i + 1}
                </span>
                <code className="font-mono" style={{ color: i === 0 ? "var(--text)" : "var(--muted)" }}>{m}</code>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* API Key */}
      {needsApiKey && (
        <section className="mb-4">
          <label className="section-label block mb-2">
            API Key
          </label>
          <div className="relative">
            <input
              type={showKey ? "text" : "password"}
              className="input pr-10"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={
                provider === "anthropic"
                  ? "sk-ant-..."
                  : provider === "gemini"
                  ? "AIzaSy..."
                  : provider === "openrouter"
                  ? "sk-or-v1-..."
                  : "sk-..."
              }
            />
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-xs"
              style={{ color: "var(--muted)" }}
              onClick={() => setShowKey((v) => !v)}
            >
              {showKey ? "hide" : "show"}
            </button>
          </div>
          <p className="text-xs mt-1.5" style={{ color: "var(--muted-2)" }}>
            Stored in browser localStorage. Never sent to this server unencrypted
            unless you click Save.
          </p>
        </section>
      )}

      {/* Model */}
      <section className="mb-4">
        <label className="section-label block mb-2">Model</label>
        <input
          type="text"
          className="input"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          placeholder={
            provider === "anthropic"
              ? "claude-sonnet-4-6"
              : provider === "openai"
              ? "gpt-4o"
              : provider === "gemini"
              ? "gemini-2.0-flash"
              : provider === "openrouter"
              ? "leave blank for auto-fallback chain"
              : "llama3.2"
          }
        />
      </section>

      {/* Base URL */}
      {needsBaseUrl && (
        <section className="mb-4">
          <label className="section-label block mb-2">
            Base URL{" "}
            <span style={{ color: "var(--muted-2)", fontStyle: "italic" }}>
              (optional for OpenAI)
            </span>
          </label>
          <input
            type="text"
            className="input"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder={
              provider === "ollama"
                ? "http://localhost:11434"
                : "https://api.openai.com/v1"
            }
          />
          {provider === "openai" && (
            <p className="text-xs mt-1.5" style={{ color: "var(--muted-2)" }}>
              Leave blank for OpenAI. Set to your local endpoint for compatible
              providers (LM Studio, vLLM, etc.)
            </p>
          )}
        </section>
      )}

      {/* Test result */}
      {testState !== "idle" && (
        <div
          className="rounded-lg px-4 py-3 mb-4 text-sm animate-in"
          style={{
            background:
              testState === "ok"
                ? "rgba(34,197,94,0.08)"
                : testState === "error"
                ? "rgba(239,68,68,0.08)"
                : "var(--surface)",
            border: `1px solid ${
              testState === "ok"
                ? "rgba(34,197,94,0.2)"
                : testState === "error"
                ? "rgba(239,68,68,0.2)"
                : "var(--border)"
            }`,
            color:
              testState === "ok"
                ? "#4ade80"
                : testState === "error"
                ? "#f87171"
                : "var(--muted)",
          }}
        >
          {testState === "testing" && (
            <span className="dot-pulse">
              <span /><span /><span />
            </span>
          )}
          {testState === "ok" && `✓ Connected — "${testMsg}"`}
          {testState === "error" && `✗ ${testMsg}`}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-3 mt-6">
        <button
          className="btn btn-primary"
          onClick={handleSave}
          disabled={!apiKey && needsApiKey && provider !== "openai" && provider !== "openrouter"}
        >
          {saved ? "✓ Saved" : "Save"}
        </button>
        <button
          className="btn btn-ghost"
          onClick={handleTest}
          disabled={testState === "testing"}
        >
          {testState === "testing" ? "Testing…" : "Test connection"}
        </button>
        <button
          className="btn btn-danger ml-auto"
          onClick={() => {
            clearSettings();
            setApiKey("");
            setModel("");
            setBaseUrl("");
            setTestState("idle");
          }}
        >
          Clear
        </button>
      </div>
    </div>
  );
}
