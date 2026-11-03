import type {
  Assessment, AssessRequest, ExampleItem, Lang, LawResponse, Meta, SseEvent,
} from "./types";
import { mockAssess, mockGetExamples, mockGetLaw, mockGetMeta, mockMarkdown } from "./mock";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8101").replace(/\/$/, "");
export const MOCK = process.env.NEXT_PUBLIC_MOCK_API === "1";

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { signal, headers: { Accept: "application/json" } });
  if (!res.ok) throw new ApiError(`${res.status} ${res.statusText}`, res.status);
  return (await res.json()) as T;
}

export const FALLBACK_META: Pick<Meta, "law_as_of" | "checked_at"> = { law_as_of: "2026-07-27", checked_at: "2026-11-03" };

export async function getMeta(): Promise<Meta> {
  if (MOCK) return mockGetMeta();
  return getJson<Meta>("/api/meta");
}

export async function getExamples(lang: Lang): Promise<ExampleItem[]> {
  if (MOCK) return mockGetExamples(lang);
  const r = await getJson<{ examples: ExampleItem[] }>(`/api/examples?lang=${lang}`);
  return r.examples;
}

export async function getLaw(id: string, lang: Lang, signal?: AbortSignal): Promise<LawResponse> {
  if (MOCK) return mockGetLaw(id, lang);
  return getJson<LawResponse>(`/api/law/${encodeURIComponent(id)}?lang=${lang}`, signal);
}

/** Parse a `text/event-stream` body into typed events. Handles chunk boundaries and CRLF. */
export async function* parseSse(body: ReadableStream<Uint8Array>): AsyncGenerator<SseEvent> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
      let idx: number;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        const ev = parseFrame(frame);
        if (ev) yield ev;
      }
    }
    if (buffer.trim()) {
      const ev = parseFrame(buffer);
      if (ev) yield ev;
    }
  } finally {
    reader.releaseLock();
  }
}

function parseFrame(frame: string): SseEvent | null {
  let name = "message";
  const data: string[] = [];
  for (const line of frame.split("\n")) {
    if (line.startsWith(":")) continue; // comment / keep-alive
    if (line.startsWith("event:")) name = line.slice(6).trim();
    else if (line.startsWith("data:")) data.push(line.slice(5).replace(/^ /, ""));
  }
  if (!data.length) return null;
  let payload: Record<string, unknown>;
  try {
    payload = JSON.parse(data.join("\n")) as Record<string, unknown>;
  } catch {
    return null;
  }
  return { ...payload, type: name } as SseEvent;
}

/** POST /api/assess, streaming events. Uses fetch (not EventSource) because the body is POSTed. */
export async function* assess(req: AssessRequest, signal?: AbortSignal): AsyncGenerator<SseEvent> {
  if (MOCK) {
    yield* mockAssess(req, signal);
    return;
  }
  const res = await fetch(`${API_URL}/api/assess`, {
    method: "POST",
    signal,
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(req),
  });
  if (!res.ok || !res.body) throw new ApiError(`${res.status} ${res.statusText}`, res.status);
  yield* parseSse(res.body);
}

async function postBlob(path: string, assessment: Assessment): Promise<Blob> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ assessment }),
  });
  if (!res.ok) throw new ApiError(`${res.status} ${res.statusText}`, res.status);
  return res.blob();
}

export async function exportMarkdown(a: Assessment): Promise<Blob> {
  if (MOCK) return new Blob([mockMarkdown(a)], { type: "text/markdown" });
  return postBlob("/api/export/markdown", a);
}

/** Returns null in mock mode (the caller falls back to the browser print dialog). */
export async function exportPdf(a: Assessment): Promise<Blob | null> {
  if (MOCK) return null;
  return postBlob("/api/export/pdf", a);
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
