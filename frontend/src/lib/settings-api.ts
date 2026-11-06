import { API_URL, ApiError, MOCK } from "./api";

export type ModelKind = "subscription" | "api_key" | "local";

export interface ModelOption {
  id: string;
  label: string;
  kind: ModelKind;
  blurb: string;
  key_url: string | null;
  needs_key: boolean;
  has_key: boolean;
  key_hint: string | null;
  model: string;
  model_hint: string;
  suggestions: string[];
  ready: boolean;
  status: string;
  active: boolean;
}

export interface ModelSettings {
  active: string;
  providers: ModelOption[];
}

export interface TestResult {
  ok: boolean;
  model?: string;
  error?: string;
  latency_s: number;
}

export interface ModelUpdate {
  target: string;
  api_key?: string;
  model?: string;
  activate?: boolean;
}

// ------------------------------------------------------------------ mock mode (no backend)

const base = { key_url: null, needs_key: false, has_key: false, key_hint: null, suggestions: [] as string[], active: false };
let mockState: ModelSettings = {
  active: "claude_cli",
  providers: [
    { ...base, id: "claude_cli", label: "Claude subscription", kind: "subscription", blurb: "Uses Claude Code signed in on this computer (Pro or Max plan). No key needed.", model: "sonnet", model_hint: "sonnet, opus or haiku", suggestions: ["sonnet", "opus", "haiku"], ready: true, status: "Claude Code found", active: true },
    { ...base, id: "codex_cli", label: "ChatGPT subscription", kind: "subscription", blurb: "Uses OpenAI's Codex CLI signed in with your ChatGPT account. No key needed.", model: "", model_hint: "empty = Codex default", ready: false, status: "Codex CLI is not installed" },
    { ...base, id: "anthropic_api", label: "Anthropic API key", kind: "api_key", blurb: "Pay per use with a key from the Claude Console.", key_url: "https://console.anthropic.com/settings/keys", needs_key: true, model: "claude-sonnet-5-5", model_hint: "a model id", suggestions: ["claude-sonnet-5-5", "claude-opus-5-5"], ready: false, status: "No key yet" },
    { ...base, id: "openai_api", label: "OpenAI API key", kind: "api_key", blurb: "Pay per use with a key from the OpenAI platform.", key_url: "https://platform.openai.com/api-keys", needs_key: true, model: "", model_hint: "a model id from your dashboard", ready: false, status: "No key yet" },
    { ...base, id: "nvidia", label: "NVIDIA API key", kind: "api_key", blurb: "Free developer key for open models (Llama, Nemotron).", key_url: "https://build.nvidia.com/settings/api-keys", needs_key: true, model: "meta/llama-3.3-70b-instruct", model_hint: "e.g. meta/llama-3.3-70b-instruct", ready: false, status: "No key yet" },
    { ...base, id: "local_mlx", label: "Local model (offline)", kind: "local", blurb: "Runs a Qwen model on this Mac with MLX. Free and private, slower and less sharp.", model: "mlx-community/Qwen2.5-14B-Instruct-4bit", model_hint: "an MLX model id", ready: true, status: "Runs on this Mac" },
  ],
};

function mockUpdate(u: ModelUpdate): ModelSettings {
  const providers = mockState.providers.map((p) => {
    if (p.id !== u.target) return p;
    const next = { ...p };
    if (u.api_key !== undefined) {
      next.has_key = u.api_key !== "";
      next.key_hint = next.has_key ? `${u.api_key.slice(0, 3)}…${u.api_key.slice(-4)}` : null;
    }
    if (u.model !== undefined) next.model = u.model;
    if (next.kind === "api_key") {
      next.ready = next.has_key && next.model !== "";
      next.status = !next.has_key ? "No key yet" : next.model ? "Key saved" : "Key saved, pick a model";
    }
    return next;
  });
  const active = u.activate ? u.target : mockState.active;
  mockState = { active, providers: providers.map((p) => ({ ...p, active: p.id === active })) };
  return mockState;
}

// ------------------------------------------------------------------ real API

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/settings/llm${path}`, {
      ...init,
      headers: init?.body ? { "Content-Type": "application/json", Accept: "application/json" } : { Accept: "application/json" },
    });
  } catch {
    throw new ApiError("The API is not reachable. Start it with ./start.sh", 0);
  }
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const j = (await res.json()) as { detail?: unknown };
      if (typeof j.detail === "string") msg = j.detail;
    } catch {
      /* not JSON */
    }
    throw new ApiError(msg, res.status);
  }
  return (await res.json()) as T;
}

export const getModelSettings = (): Promise<ModelSettings> => (MOCK ? Promise.resolve(mockState) : call(""));

export const updateModelSettings = (u: ModelUpdate): Promise<ModelSettings> =>
  MOCK ? Promise.resolve(mockUpdate(u)) : call("", { method: "PUT", body: JSON.stringify(u) });

export const testModel = (id: string): Promise<TestResult> => {
  if (!MOCK) return call(`/test/${encodeURIComponent(id)}`, { method: "POST" });
  const p = mockState.providers.find((x) => x.id === id);
  if (p?.needs_key && !p.has_key) return Promise.resolve({ ok: false, error: "No API key saved yet.", latency_s: 0 });
  if (p && !p.ready) return Promise.resolve({ ok: false, error: `${p.status}.`, latency_s: 0 });
  return Promise.resolve({ ok: true, model: p?.model || "mock", latency_s: 0.1 });
};
