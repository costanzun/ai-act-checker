"""Render the README evaluation table from the latest eval results (one row per configuration).

    backend/.venv/bin/python scripts/fill_readme_eval.py          # rewrite the table in README.md
    backend/.venv/bin/python scripts/fill_readme_eval.py --print  # just print the rows

Keeps README.md consistent with eval/results/*.json (latest file per config wins).
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results"
README = ROOT / "README.md"

ROWS = [
    ("hybrid:claude_cli:sonnet", "hybrid · Claude Sonnet (CLI)"),
    ("hybrid:local_mlx:mlx-community/Qwen2.5-14B-Instruct-4bit", "hybrid · Qwen2.5-14B-Instruct-4bit (local)"),
    ("hybrid:local_mlx:mlx-community/Qwen2.5-3B-Instruct-4bit", "hybrid · Qwen2.5-3B-Instruct-4bit (local)"),
    ("baseline:claude_cli:sonnet", "baseline (pure LLM+RAG) · Claude Sonnet"),
    ("baseline:local_mlx:mlx-community/Qwen2.5-14B-Instruct-4bit", "baseline · Qwen2.5-14B"),
]

HEADER = "| Configuration | Tier accuracy | Under-classified | Asked when needed | Citation validity | Citation recall | p50 latency (uncached) | Cost / assessment |"
SEP = "|---|---|---|---|---|---|---|---|"


def latest() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in sorted(RESULTS.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if "config" in d and "summary" in d:
            d["_file"] = p.name
            out[d["config"]] = d
    return out


def pct(x: float | None) -> str:
    return "–" if x is None else f"{x:.0%}"


def row(label: str, d: dict | None) -> str:
    if d is None:
        return f"| {label} | not run | – | – | – | – | – | – |"
    s = d["summary"]
    acc = f"{s['tier_correct']}/{s['n']} ({pct(s['tier_accuracy'])})"
    err = f" · {s['n_errors']} errors" if s.get("n_errors") else ""
    lat_ms = s.get("latency_uncached_p50_ms") or s.get("latency_p50_ms")
    lat = "–" if lat_ms is None else f"{lat_ms/1000:.0f} s"
    cost = "$0 (local)" if d["provider"] == "local_mlx" else ("–" if s["mean_cost_usd"] is None else f"${s['mean_cost_usd']:.3f}")
    asked = pct(s["asked_when_should"]) if d["mode"] == "hybrid" else "n/a"
    validity = pct(s["citation_validity"]) + (" (by construction)" if d["mode"] == "hybrid" else "")
    return f"| {label} | {acc}{err} | {pct(s['under_classification_rate'])} | {asked} | {validity} | {pct(s['citation_recall'])} | {lat} | {cost} |"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args()
    data = latest()
    lines = [HEADER, SEP] + [row(label, data.get(cfg)) for cfg, label in ROWS]
    table = "\n".join(lines)
    if a.print:
        print(table)
        return
    s = README.read_text(encoding="utf-8")
    pattern = re.compile(r"\| Configuration \| Tier accuracy \|.*?(?=\n\n)", re.S)
    assert pattern.search(s), "README table not found"
    s = pattern.sub(table, s, count=1)
    README.write_text(s, encoding="utf-8")
    print("README table updated:")
    print(table)


if __name__ == "__main__":
    main()
