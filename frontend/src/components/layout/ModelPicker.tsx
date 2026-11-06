"use client";

import { useEffect, useState } from "react";
import { Bot, Check, CircleAlert, Copy, ExternalLink, Loader2, X, Zap } from "lucide-react";
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { DogScene } from "@/components/pixel/Pixel";
import { useT } from "@/i18n";
import type { DictKey } from "@/i18n/en";
import { MOCK } from "@/lib/api";
import {
  getModelSettings, testModel, updateModelSettings,
  type ModelKind, type ModelOption, type ModelSettings, type TestResult,
} from "@/lib/settings-api";
import { cn } from "@/lib/utils";

type T = ReturnType<typeof useT>["t"];

/** Terminal steps shown when a subscription CLI is missing. Shown as text, never run. */
const SETUP: Record<string, string[]> = {
  claude_cli: ["curl -fsSL https://claude.ai/install.sh | bash", "claude"],
  codex_cli: ["npm install -g @openai/codex", "codex login"],
};

const GROUPS: ModelKind[] = ["subscription", "api_key", "local"];
const KNOWN = ["claude_cli", "codex_cli", "anthropic_api", "openai_api", "nvidia", "local_mlx"];

/** Localised text for a provider field; falls back to the backend's English for unknown ids. */
function text(t: T, kind: "short" | "label" | "blurb", p: Pick<ModelOption, "id" | "label" | "blurb">): string {
  if (!KNOWN.includes(p.id)) return kind === "blurb" ? p.blurb : p.label;
  return t(`model.${kind}.${p.id}` as DictKey);
}

function statusText(t: T, p: ModelOption): string {
  if (p.id === "claude_cli") return t(p.ready ? "model.status.claudeFound" : "model.status.claudeMissing");
  if (p.id === "codex_cli") return t(p.ready ? "model.status.codexFound" : "model.status.codexMissing");
  if (p.kind === "api_key") return t(!p.has_key ? "model.status.noKey" : p.model ? "model.status.keySaved" : "model.status.pickModel");
  if (p.kind === "local") return t("model.status.local");
  return p.status;
}

const field = "h-11 min-w-0 rounded-full border-2 border-foreground bg-card px-4 font-mono text-[13px] outline-none focus-visible:shadow-[0_0_0_4px_var(--sun)]";

function CopyCmd({ cmd }: { cmd: string }) {
  const { t } = useT();
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      onClick={() => navigator.clipboard?.writeText(cmd).then(() => { setDone(true); setTimeout(() => setDone(false), 1200); }, () => {})}
      className="group flex w-full items-center justify-between gap-2 rounded-xl bg-foreground px-3 py-2 text-left font-mono text-[12.5px] text-background"
      aria-label={t("model.copy", { cmd })}
    >
      <span className="truncate">$ {cmd}</span>
      {done ? <Check className="size-3.5 shrink-0" aria-hidden /> : <Copy className="size-3.5 shrink-0 opacity-60 group-hover:opacity-100" aria-hidden />}
    </button>
  );
}

function Option({ p, open, onOpen, onSaved }: { p: ModelOption; open: boolean; onOpen: () => void; onSaved: (s: ModelSettings) => void }) {
  const { t } = useT();
  const [key, setKey] = useState("");
  const [model, setModel] = useState(p.model);
  const [busy, setBusy] = useState<"save" | "use" | "test" | null>(null);
  const [test, setTest] = useState<TestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const editModel = p.kind !== "local";
  const dirty = key !== "" || model !== p.model;
  const status = statusText(t, p);
  const label = text(t, "label", p);

  async function save(activate: boolean) {
    setBusy(activate ? "use" : "save");
    setError(null);
    try {
      onSaved(await updateModelSettings({ target: p.id, ...(key ? { api_key: key } : {}), ...(editModel && model !== p.model ? { model } : {}), activate }));
      setKey("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  async function runTest() {
    setBusy("test");
    setTest(null);
    try {
      setTest(await testModel(p.id));
    } catch (e) {
      setTest({ ok: false, error: (e as Error).message, latency_s: 0 });
    } finally {
      setBusy(null);
    }
  }

  async function removeKey() {
    setError(null);
    try {
      onSaved(await updateModelSettings({ target: p.id, api_key: "" }));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div
      data-testid={`model-${p.id}`}
      data-active={p.active || undefined}
      className={cn("rounded-2xl border-2 transition-colors", p.active ? "border-foreground bg-sun-soft dark:bg-white/[0.06]" : "border-foreground/25")}
    >
      <button type="button" onClick={onOpen} className="flex w-full items-center gap-3 px-4 py-3 text-left" aria-expanded={open}>
        <span className={cn("flex size-5 shrink-0 items-center justify-center rounded-full border-2 border-foreground", p.active && "bg-foreground text-background")}>
          {p.active && <Check className="size-3" strokeWidth={3} aria-hidden />}
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-x-2 text-[15px] font-bold">
            {label}
            {p.active && <span className="pixel-label text-[10.5px]">· {t("model.inUse")}</span>}
          </span>
          <span className="block text-[12.5px] text-muted-foreground">{text(t, "blurb", p)}</span>
          <span className={cn("mt-1 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11.5px] font-semibold sm:hidden", p.ready ? "bg-pass/12 text-pass" : "bg-muted text-muted-foreground")}>
            {p.ready ? <Check className="size-3" aria-hidden /> : <CircleAlert className="size-3" aria-hidden />}
            {status}
          </span>
        </span>
        <span className={cn("hidden shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[11.5px] font-semibold sm:inline-flex", p.ready ? "bg-pass/12 text-pass" : "bg-muted text-muted-foreground")}>
          {p.ready ? <Check className="size-3" aria-hidden /> : <CircleAlert className="size-3" aria-hidden />}
          {status}
        </span>
      </button>

      {open && (
        <div className="space-y-3 border-t-2 border-dashed border-foreground/25 px-4 pb-4 pt-3">
          {!p.ready && SETUP[p.id] && (
            <div className="space-y-2">
              <p className="text-[13px]">{t(`model.setup.${p.id}` as DictKey)} {t("model.setup.run")}</p>
              {SETUP[p.id].map((c) => <CopyCmd key={c} cmd={c} />)}
            </div>
          )}

          {p.needs_key && (
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 text-[13px] font-bold">
                <label htmlFor={`key-${p.id}`}>
                  {t("model.apiKey")}{" "}
                  {p.key_hint && <span className="font-mono font-normal text-muted-foreground">{t("model.keySaved", { hint: p.key_hint })}</span>}
                </label>
                {p.key_url && (
                  <a href={p.key_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[12.5px] font-semibold underline underline-offset-2">
                    {t("model.getKey")} <ExternalLink className="size-3" aria-hidden />
                  </a>
                )}
              </div>
              <div className="flex gap-2">
                <input
                  id={`key-${p.id}`}
                  type="password"
                  autoComplete="off"
                  spellCheck={false}
                  value={key}
                  onChange={(e) => setKey(e.target.value)}
                  placeholder={p.has_key ? t("model.keyReplace") : t("model.keyPlaceholder")}
                  className={cn(field, "flex-1")}
                  data-testid={`key-${p.id}`}
                />
                {p.has_key && (
                  <button type="button" onClick={removeKey} className="pill pill-secondary h-11 shrink-0 px-4 text-[12.5px]">
                    {t("model.remove")}
                  </button>
                )}
              </div>
            </div>
          )}

          {editModel && (
            <div className="space-y-1.5">
              <label htmlFor={`model-input-${p.id}`} className="block text-[13px] font-bold">
                {t("model.model")} {p.model_hint && <span className="font-normal text-muted-foreground">({p.model_hint})</span>}
              </label>
              <input
                id={`model-input-${p.id}`}
                value={model}
                onChange={(e) => setModel(e.target.value)}
                spellCheck={false}
                placeholder={p.id === "codex_cli" ? t("model.codexDefault") : t("model.modelPlaceholder")}
                className={cn(field, "w-full")}
                data-testid={`model-input-${p.id}`}
              />
              {p.suggestions.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {p.suggestions.map((s) => (
                    <button key={s} type="button" aria-pressed={model === s} onClick={() => setModel(s)}
                      className={cn("rounded-full border-2 border-foreground px-2.5 py-0.5 font-mono text-[12px]", model === s ? "bg-foreground text-background" : "bg-card")}>
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {test && (
            <p role="status" data-testid="model-test"
              className={cn("rounded-xl px-3 py-2 text-[12.5px] font-medium", test.ok ? "bg-pass/12 text-pass" : "bg-fail/10 text-fail")}>
              {test.ok ? t("model.connected", { model: test.model ?? "", s: test.latency_s }) : test.error}
            </p>
          )}
          {error && <p role="alert" className="rounded-xl bg-fail/10 px-3 py-2 text-[12.5px] font-medium text-fail">{error}</p>}

          <div className="flex flex-wrap items-center gap-2">
            {(p.needs_key || editModel) && (
              <button type="button" disabled={!dirty || busy !== null} onClick={() => save(false)} className="pill pill-secondary h-10 px-4 text-[13px]" data-testid={`save-${p.id}`}>
                {busy === "save" && <Loader2 className="size-3.5 animate-spin" aria-hidden />} {t("model.save")}
              </button>
            )}
            <button type="button" disabled={busy !== null || (p.needs_key && !p.has_key)} onClick={runTest} className="pill pill-secondary h-10 px-4 text-[13px]" data-testid={`test-${p.id}`}>
              {busy === "test" ? <Loader2 className="size-3.5 animate-spin" aria-hidden /> : <Zap className="size-3.5" aria-hidden />} {t("model.test")}
            </button>
            {!p.active && (
              <button
                type="button"
                disabled={busy !== null || (!p.ready && !(p.needs_key && key))}
                onClick={() => save(true)}
                className="pill pill-primary ml-auto h-10 px-5 text-[13px]"
                data-testid={`use-${p.id}`}
              >
                {busy === "use" && <Loader2 className="size-3.5 animate-spin" aria-hidden />} {t("model.use")}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/** "Who does the sniffing?": pick the model behind the reading and the explanation. */
function ModelDialog({ open, onOpenChange, onChanged }: { open: boolean; onOpenChange: (o: boolean) => void; onChanged: (s: ModelSettings) => void }) {
  const { t } = useT();
  const [s, setS] = useState<ModelSettings | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  // Mounted only while open (see ModelPicker), so this loads fresh settings each time.
  useEffect(() => {
    getModelSettings().then((x) => {
      setS(x);
      setExpanded(x.active);
    }, (e) => setErr((e as Error).message));
  }, []);

  const saved = (x: ModelSettings) => {
    setS(x);
    onChanged(x);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        showCloseButton={false}
        data-testid="model-dialog"
        className="flex max-h-[min(90dvh,800px)] w-[min(640px,calc(100vw-24px))] max-w-none flex-col gap-0 overflow-hidden rounded-[1.6rem] border-2 border-foreground bg-card p-0 text-foreground ring-0 sm:max-w-none"
      >
        <div className="px-block m-2 flex items-end gap-3 overflow-hidden rounded-[1.2rem] px-4 pt-4 sm:px-5"
          style={{ "--block": "var(--block-loading)", "--grid": "4px" } as React.CSSProperties}>
          <div className="min-w-0 flex-1 pb-4">
            <p className="pixel-label">{t("model.eyebrow")}</p>
            <DialogTitle className="display mt-1.5 text-[26px] font-black leading-[0.95] sm:text-[34px]">{t("model.title")}</DialogTitle>
          </div>
          <DogScene scene="loading" label={t("model.scene")} className="w-[110px] shrink-0 sm:w-[150px]" />
          <DialogClose aria-label={t("model.close")} className="absolute right-4 top-4 inline-flex size-9 items-center justify-center rounded-full border-2 border-foreground bg-card text-foreground">
            <X className="size-4" aria-hidden />
          </DialogClose>
        </div>
        <div className="scroll-thin min-h-0 flex-1 space-y-5 overflow-y-auto px-4 pb-5 pt-2 sm:px-5">
          <DialogDescription className="text-[13.5px] text-muted-foreground">{t("model.lede")}</DialogDescription>
          {err && <p role="alert" className="rounded-xl bg-fail/10 px-3 py-2 text-[13px] font-medium text-fail">{err}</p>}
          {!s && !err && <Loader2 className="mx-auto my-10 size-6 animate-spin text-muted-foreground" aria-hidden />}
          {s && GROUPS.map((kind) => {
            const list = s.providers.filter((p) => p.kind === kind);
            if (!list.length) return null;
            return (
              <section key={kind} className="space-y-2">
                <h3 className="pixel-label text-[12px]">{t(`model.group.${kind}` as DictKey)}</h3>
                {list.map((p) => (
                  <Option key={`${p.id}:${p.model}:${p.key_hint ?? ""}`} p={p} open={expanded === p.id}
                    onOpen={() => setExpanded((e) => (e === p.id ? null : p.id))} onSaved={saved} />
                ))}
              </section>
            );
          })}
          {s && <p className="text-[11.5px] text-muted-foreground">{t("model.footer")}</p>}
        </div>
      </DialogContent>
    </Dialog>
  );
}

/** Header pill: which model is in use, with a red dot when it is not set up. Opens the dialog. */
export function ModelPicker() {
  const { t } = useT();
  const [s, setS] = useState<ModelSettings | null>(null);
  const [down, setDown] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    getModelSettings().then((x) => { setS(x); setDown(false); }, () => setDown(true));
  }, []);

  const active = s?.providers.find((p) => p.id === s.active);
  const name = active ? text(t, "short", active) : s?.active ?? "";
  const label = MOCK ? t("model.pillMock") : down ? t("model.pillOffline") : !s ? "AI" : active?.ready ? t("model.pill", { name }) : t("model.pillNotReady", { name });
  const dot = down || (s && !active?.ready) ? "bg-fail" : s ? "bg-pass" : "bg-muted-foreground/50";

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        title={t("model.buttonTitle")}
        aria-label={`${label}. ${t("model.buttonTitle")}`}
        data-testid="model-pill"
        data-ready={active?.ready ? "true" : "false"}
        className="inline-flex h-10 shrink-0 items-center gap-1.5 rounded-full border-2 border-foreground bg-card px-3 text-[12.5px] font-bold text-foreground transition-colors hover:bg-sun-soft max-sm:w-10 max-sm:justify-center max-sm:px-0"
      >
        <span className="relative inline-flex">
          <Bot className="size-4" aria-hidden />
          <span className={cn("absolute -right-1 -top-0.5 size-2 rounded-full ring-2 ring-card", dot)} aria-hidden />
        </span>
        <span className="hidden max-w-[180px] truncate sm:inline">{label}</span>
      </button>
      {open && <ModelDialog open onOpenChange={setOpen} onChanged={setS} />}
    </>
  );
}
