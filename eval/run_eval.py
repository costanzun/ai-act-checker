"""Reproducible evaluation of the EU AI Act Checker.

Usage (from the project root):
    backend/.venv/bin/python eval/run_eval.py --config all
    backend/.venv/bin/python eval/run_eval.py --config hybrid:claude_cli:sonnet --limit 5
    backend/.venv/bin/python eval/run_eval.py --config baseline:local_mlx:mlx-community/Qwen2.5-14B-Instruct-4bit
    backend/.venv/bin/python eval/run_eval.py --report-only   # regenerate REPORT.md from eval/results

A configuration is ``<mode>:<provider>:<model>`` where mode is ``hybrid``
(facts → rule engine → cited narrative; the product flow) or ``baseline``
(pure LLM + retrieved provisions; the comparison point).

Metrics per configuration (see PLAN.md §5): tier accuracy, under-classification
rate, question behaviour, citation validity, citation recall, latency, tokens,
cost. Results are written to ``eval/results/<timestamp>-<config>.json`` and
summarised in ``eval/REPORT.md``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.chdir(ROOT)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
os.environ.setdefault("HF_HOME", str(ROOT / "data" / "models"))

from app.corpus.store import CorpusStore  # noqa: E402
from app.engine.facts import FactSheet  # noqa: E402
from app.engine.models import Question  # noqa: E402
from app.llm import LLMError, get_provider, parse_json_object  # noqa: E402
from app.pipeline import CITE_RE, Pipeline  # noqa: E402
from app.prompts import baseline_messages  # noqa: E402

RESULTS = ROOT / "eval" / "results"
CASES = ROOT / "eval" / "cases.yaml"
REPORT = ROOT / "eval" / "REPORT.md"

TIER_ORDER = {"out_of_scope": 0, "minimal_risk": 1, "limited_risk": 2, "high_risk": 3, "prohibited": 4}

DEFAULT_CONFIGS = [
    "hybrid:claude_cli:sonnet",
    "hybrid:local_mlx:mlx-community/Qwen2.5-14B-Instruct-4bit",
    "hybrid:local_mlx:mlx-community/Qwen2.5-3B-Instruct-4bit",
    "baseline:claude_cli:sonnet",
    "baseline:local_mlx:mlx-community/Qwen2.5-14B-Instruct-4bit",
]


# ----------------------------------------------------------------------------- helpers
def load_cases(limit: int | None = None, ids: list[str] | None = None) -> list[dict[str, Any]]:
    cases = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    if ids:
        cases = [c for c in cases if c["id"] in set(ids)]
    return cases[:limit] if limit else cases


def nested_get(d: dict[str, Any], path: str) -> Any:
    """Facts in cases.yaml may be flat ("art63.profiling_of_natural_persons": true) or nested."""
    if path in d:
        return d[path]
    node: Any = d
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def make_answer_fn(case: dict[str, Any]):
    facts = case.get("facts") or {}

    def answer(q: Question) -> Any:
        return nested_get(facts, q.fact_path)

    return answer


def citation_metrics(cited: list[str], expected: list[str], store: CorpusStore) -> dict[str, Any]:
    cited_u = list(dict.fromkeys(cited))
    valid = [c for c in cited_u if store.exists(c)]
    hit = [e for e in expected if any(c == e or c.startswith(e + ".") for c in cited_u)]
    return {
        "cited": cited_u,
        "n_cited": len(cited_u),
        "n_valid": len(valid),
        "validity": (len(valid) / len(cited_u)) if cited_u else None,
        "recall": (len(hit) / len(expected)) if expected else None,
        "missing": [e for e in expected if e not in hit],
    }


def assessment_citations(a: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for f in a["classification"]["findings"]:
        ids += f["citations"]
    ids += CITE_RE.findall(a["reasoning_md"])
    for o in a["obligations"]:
        ids += o["citations"]
    return ids


# ----------------------------------------------------------------------------- runners
async def run_hybrid(pipeline: Pipeline, case: dict[str, Any], provider: str, model: str, store: CorpusStore) -> dict[str, Any]:
    t0 = time.perf_counter()
    err = None
    assessment = None
    trace: dict[str, Any] = {}
    try:
        assessment, trace = await pipeline.assess_blocking(
            case["description"], language=case.get("language", "en"), answer_fn=make_answer_fn(case), provider=provider, model=model
        )
    except LLMError as exc:
        err = str(exc)
    latency = int((time.perf_counter() - t0) * 1000)
    row: dict[str, Any] = {
        "id": case["id"],
        "expected_tier": case["expected_tier"],
        "expected_overlays": sorted(case.get("expected_overlays") or []),
        "should_ask": bool(case.get("should_ask")),
        "latency_ms": latency,
        "rounds": trace.get("rounds", 0),
        "questions": trace.get("questions", []),
        "error": err,
    }
    if assessment is None:
        row.update({"tier": None, "overlays": [], "correct": False, "under": None, "asked": bool(trace.get("questions"))})
        return row
    a = assessment.model_dump()
    overlays = sorted(k for k, v in a["classification"]["overlays"].items() if v)
    row.update(
        {
            "tier": a["classification"]["tier"],
            "confidence": a["classification"]["confidence"],
            "overlays": overlays,
            "role": a["classification"]["role"],
            "correct": a["classification"]["tier"] == case["expected_tier"],
            "overlays_correct": overlays == row["expected_overlays"],
            "under": TIER_ORDER[a["classification"]["tier"]] < TIER_ORDER[case["expected_tier"]],
            "asked": bool(trace.get("questions")),
            "citations": citation_metrics(assessment_citations(a), case.get("expected_citations") or [], store),
            "stripped_citations": a["metrics"]["stripped_citations"],
            "unverified_references": a["metrics"].get("unverified_references", 0),
            "llm_calls": a["metrics"]["llm_calls"],
            "input_tokens": a["metrics"]["input_tokens"],
            "output_tokens": a["metrics"]["output_tokens"],
            "cost_usd": a["metrics"]["cost_usd"],
            "cached": a["metrics"]["cached"],
            "facts": a["facts"],
            "reasoning_md": a["reasoning_md"],
        }
    )
    return row


async def run_baseline(pipeline: Pipeline, case: dict[str, Any], provider_name: str, model: str, store: CorpusStore) -> dict[str, Any]:
    t0 = time.perf_counter()
    prov = get_provider(provider_name, model)
    lang = case.get("language", "en")
    ctx: dict[str, str] = {}
    r = pipeline.retriever
    if r is not None:
        hits = r.search(case["description"], lang=lang, k=10, candidates=40)
        ctx = {h["id"]: store.full_text(h["id"], lang) for h in hits if store.exists(h["id"])}
    row: dict[str, Any] = {
        "id": case["id"],
        "expected_tier": case["expected_tier"],
        "expected_overlays": sorted(case.get("expected_overlays") or []),
        "should_ask": bool(case.get("should_ask")),
        "retrieved": list(ctx),
    }
    try:
        res = await prov.complete(baseline_messages(case["description"], ctx), temperature=0.0, max_tokens=900, json_mode=True)
        data = parse_json_object(res.text)
        tier = data.get("tier")
        if tier not in TIER_ORDER:
            tier = None
        overlays = sorted(o for o in (data.get("overlays") or []) if o in {"transparency_art50", "gpai"})
        cited = [str(c) for c in (data.get("citations") or [])]
        row.update(
            {
                "tier": tier,
                "confidence": data.get("confidence"),
                "overlays": overlays,
                "role": data.get("role"),
                "correct": tier == case["expected_tier"],
                "overlays_correct": overlays == row["expected_overlays"],
                "under": (TIER_ORDER[tier] < TIER_ORDER[case["expected_tier"]]) if tier else True,
                "asked": False,
                "citations": citation_metrics(cited, case.get("expected_citations") or [], store),
                "llm_calls": 1,
                "input_tokens": res.input_tokens or 0,
                "output_tokens": res.output_tokens or 0,
                "cost_usd": res.cost_usd or 0.0,
                "cached": res.cached,
                "reasoning_md": data.get("reasoning", ""),
                "error": None,
            }
        )
    except Exception as exc:
        row.update({"tier": None, "overlays": [], "correct": False, "under": None, "asked": False, "error": str(exc)[:300]})
    row["latency_ms"] = int((time.perf_counter() - t0) * 1000)
    return row


def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    ok = [r for r in rows if r.get("error") is None and r.get("tier")]
    acc = sum(1 for r in rows if r.get("correct")) / n if n else 0  # errors count as wrong answers
    under = (sum(1 for r in ok if r.get("under")) / len(ok)) if ok else None  # rate over completed runs
    overlays_acc = (sum(1 for r in ok if r.get("overlays_correct")) / len(ok)) if ok else None
    ask_rows = [r for r in rows if r["should_ask"]]
    noask_rows = [r for r in rows if not r["should_ask"]]
    asked_when_should = (sum(1 for r in ask_rows if r.get("asked")) / len(ask_rows)) if ask_rows else None
    silent_when_complete = (sum(1 for r in noask_rows if not r.get("asked")) / len(noask_rows)) if noask_rows else None
    validity = [r["citations"]["validity"] for r in ok if r.get("citations") and r["citations"]["validity"] is not None]
    recall = [r["citations"]["recall"] for r in ok if r.get("citations") and r["citations"]["recall"] is not None]
    lat = [r["latency_ms"] for r in ok if r.get("latency_ms") is not None]
    lat_uncached = [r["latency_ms"] for r in ok if r.get("latency_ms") is not None and not r.get("cached")]
    cost = [r.get("cost_usd") or 0.0 for r in ok]
    toks_in = [r.get("input_tokens") or 0 for r in ok]
    toks_out = [r.get("output_tokens") or 0 for r in ok]
    hard = [r for r in rows if r.get("difficulty") == "hard"]
    return {
        "n": n,
        "n_errors": sum(1 for r in rows if r.get("error")),
        "tier_accuracy": acc,
        "tier_correct": sum(1 for r in rows if r.get("correct")),
        "under_classification_rate": under,
        "overlay_accuracy": overlays_acc,
        "asked_when_should": asked_when_should,
        "silent_when_complete": silent_when_complete,
        "citation_validity": statistics.mean(validity) if validity else None,
        "citation_recall": statistics.mean(recall) if recall else None,
        "stripped_citations_total": sum(r.get("stripped_citations") or 0 for r in rows),
        "unverified_references_total": sum(r.get("unverified_references") or 0 for r in rows),
        "latency_p50_ms": statistics.median(lat) if lat else None,
        "latency_p95_ms": (sorted(lat)[max(0, int(0.95 * len(lat)) - 1)] if lat else None),
        "latency_uncached_p50_ms": statistics.median(lat_uncached) if lat_uncached else None,
        "mean_cost_usd": statistics.mean(cost) if cost else None,
        "total_cost_usd": sum(cost),
        "mean_input_tokens": statistics.mean(toks_in) if toks_in else None,
        "mean_output_tokens": statistics.mean(toks_out) if toks_out else None,
        "hard_accuracy": (sum(1 for r in hard if r.get("correct")) / len(hard)) if hard else None,
    }


async def run_config(config: str, cases: list[dict[str, Any]], concurrency: int, tag: str) -> Path:
    mode, provider, model = config.split(":", 2)
    store = CorpusStore(ROOT / "data" / "corpus")
    pipeline = Pipeline(store)
    # local models must run serially; the Claude CLI tolerates a little parallelism
    conc = 1 if provider == "local_mlx" else concurrency
    sem = asyncio.Semaphore(conc)
    results: list[dict[str, Any]] = []

    async def one(case: dict[str, Any]) -> None:
        async with sem:
            fn = run_hybrid if mode == "hybrid" else run_baseline
            row = await fn(pipeline, case, provider, model, store)
            row["difficulty"] = case.get("difficulty")
            row["source"] = case.get("source")
            row["language"] = case.get("language", "en")
            results.append(row)
            mark = "OK " if row.get("correct") else "XX "
            print(f"  {mark}{row['id']:<45} exp={row['expected_tier']:<13} got={str(row.get('tier')):<13} {row['latency_ms']:>6} ms" + (f"  ERR {row['error'][:80]}" if row.get("error") else ""), flush=True)

    print(f"\n=== {config}  ({len(cases)} cases, concurrency {conc}) ===", flush=True)
    t0 = time.perf_counter()
    await asyncio.gather(*(one(c) for c in cases))
    results.sort(key=lambda r: r["id"])
    summary = summarise(results)
    summary["wall_time_s"] = round(time.perf_counter() - t0, 1)
    out = {
        "config": config,
        "mode": mode,
        "provider": provider,
        "model": model,
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hardware": "Apple M4 Max, 48 GB" if provider == "local_mlx" else "Claude Code CLI (subscription)" if provider == "claude_cli" else provider,
        "summary": summary,
        "rows": results,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    safe = config.replace("/", "_").replace(":", "__")
    path = RESULTS / f"{tag}-{safe}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    s = summary
    print(
        f"--- {config}: tier acc {s['tier_correct']}/{s['n']} ({s['tier_accuracy']:.0%}), under-class {fmt_pct(s['under_classification_rate'])}, "
        f"cit. validity {s['citation_validity'] if s['citation_validity'] is None else f'{s['citation_validity']:.0%}'}, "
        f"cit. recall {s['citation_recall'] if s['citation_recall'] is None else f'{s['citation_recall']:.0%}'}, p50 {s['latency_p50_ms']} ms, "
        f"mean cost ${(s['mean_cost_usd'] or 0):.4f}, errors {s['n_errors']}",
        flush=True,
    )
    return path


# ----------------------------------------------------------------------------- report
def latest_results() -> dict[str, dict[str, Any]]:
    """Most recent result file per config."""
    latest: dict[str, dict[str, Any]] = {}
    for p in sorted(RESULTS.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if "config" in d and "summary" in d:
            d["_file"] = p.name
            latest[d["config"]] = d  # sorted by name = timestamp; last wins
    return latest


def fmt_pct(x: float | None) -> str:
    return "–" if x is None else f"{x:.0%}"


def fmt_ms(x: float | None) -> str:
    return "–" if x is None else f"{x/1000:.1f} s"


def fmt_usd(x: float | None) -> str:
    return "–" if x is None else f"${x:.4f}"


def write_report() -> None:
    latest = latest_results()
    if not latest:
        print("no results to report")
        return
    cases = load_cases()
    n_cases = len(cases)
    lines: list[str] = []
    lines.append("# Evaluation report\n")
    lines.append(f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by `eval/run_eval.py`. Test set: `eval/cases.yaml` ({n_cases} labelled cases; see `eval/README.md`).\n")
    lines.append("Law baseline: Regulation (EU) 2024/1689 consolidated 2026-07-27 (incl. Regulation (EU) 2026/1744).\n")
    lines.append("## Headline table\n")
    lines.append("| Configuration | Tier accuracy | Under-classified | Overlays | Asked when needed | Citation validity | Citation recall | p50 latency (uncached) | Mean cost / assessment | Errors |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for cfg, d in sorted(latest.items(), key=lambda kv: (kv[1]["mode"] != "hybrid", kv[0])):
        s = d["summary"]
        label = f"**{d['mode']}** · {d['provider']} · `{d['model'].split('/')[-1]}`"
        lines.append(
            f"| {label} | {s['tier_correct']}/{s['n']} ({fmt_pct(s['tier_accuracy'])}) | {fmt_pct(s['under_classification_rate'])} | {fmt_pct(s['overlay_accuracy'])} | {fmt_pct(s['asked_when_should'])} | {fmt_pct(s['citation_validity'])} | {fmt_pct(s['citation_recall'])} | {fmt_ms(s.get('latency_uncached_p50_ms') or s['latency_p50_ms'])} | {fmt_usd(s['mean_cost_usd'])} | {s['n_errors']} |"
        )
    lines.append("")
    lines.append("Definitions: *Tier accuracy* = exact match of the risk tier. *Under-classified* = predicted a less severe tier than the label (the dangerous error). *Overlays* = Art. 50 / GPAI overlays exactly right (among completed runs). *Asked when needed* = share of `should_ask` cases where at least one clarifying question was asked. *Citation validity* = share of cited IDs that resolve to a real provision. *Citation recall* = share of the labelled key provisions that were cited. Cost = API-equivalent USD reported by the Claude CLI (billed as subscription) or $0 for local models (Apple M4 Max). Latency is the median over assessments whose LLM calls were not served from the cache; it includes all LLM calls and question rounds.\n")
    # per-configuration detail
    for cfg, d in sorted(latest.items(), key=lambda kv: (kv[1]["mode"] != "hybrid", kv[0])):
        s = d["summary"]
        lines.append(f"## {d['mode']} · {d['provider']} · {d['model']}\n")
        lines.append(f"Run {d['run_at']} on {d['hardware']}; wall time {s.get('wall_time_s','?')} s; uncached p50 {fmt_ms(s.get('latency_uncached_p50_ms'))}; p95 {fmt_ms(s['latency_p95_ms'])}; mean tokens in/out {int(s['mean_input_tokens'] or 0)}/{int(s['mean_output_tokens'] or 0)}; hard-case accuracy {fmt_pct(s['hard_accuracy'])}; stripped (disallowed) citations {s['stripped_citations_total']}; file `{d['_file']}`.\n")
        wrong = [r for r in d["rows"] if not r.get("correct")]
        if wrong:
            lines.append("| Case | Expected | Got | Asked | Note |")
            lines.append("|---|---|---|---|---|")
            for r in wrong:
                note = (r.get("error") or "")[:80] or ("; ".join(r.get("citations", {}).get("missing", [])[:3]) and "missing: " + ", ".join(r["citations"]["missing"][:3]))
                lines.append(f"| `{r['id']}` | {r['expected_tier']} | {r.get('tier')} | {'yes' if r.get('asked') else 'no'} | {note} |")
            lines.append("")
        else:
            lines.append("All cases correct.\n")
    # breakdown by source for hybrid configs
    lines.append("## Accuracy by case source (hybrid configurations)\n")
    sources = sorted({c.get("source", "?") for c in cases})
    hybrids = [(cfg, d) for cfg, d in latest.items() if d["mode"] == "hybrid"]
    if hybrids:
        lines.append("| Source | n | " + " | ".join(f"`{d['model'].split('/')[-1]}`" for _, d in hybrids) + " |")
        lines.append("|---|---|" + "---|" * len(hybrids))
        for src in sources:
            n_src = sum(1 for c in cases if c.get("source") == src)
            cells = []
            for _, d in hybrids:
                rows = [r for r in d["rows"] if r.get("source") == src]
                cells.append(f"{sum(1 for r in rows if r.get('correct'))}/{len(rows)}" if rows else "–")
            lines.append(f"| {src} | {n_src} | " + " | ".join(cells) + " |")
        lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT}")


# ----------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", action="append", help="mode:provider:model, or 'all' (repeatable)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--ids", nargs="*", default=None, help="only these case ids")
    ap.add_argument("--concurrency", type=int, default=int(os.getenv("LLM_MAX_CONCURRENCY", "2")))
    ap.add_argument("--no-cache", action="store_true", help="disable the LLM cache for this run")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    if args.report_only:
        write_report()
        return
    if args.no_cache:
        os.environ["LLM_CACHE"] = "0"
    configs: list[str] = []
    for c in args.config or ["hybrid:claude_cli:sonnet"]:
        configs += DEFAULT_CONFIGS if c == "all" else [c]
    cases = load_cases(args.limit, args.ids)
    tag = datetime.now().strftime("%Y%m%d-%H%M%S")
    for cfg in configs:
        asyncio.run(run_config(cfg, cases, args.concurrency, tag))
    write_report()


if __name__ == "__main__":
    main()
