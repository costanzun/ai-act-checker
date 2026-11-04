"""Run an assessment from the terminal (handy for demos and debugging).

    backend/.venv/bin/python scripts/assess_cli.py "Our HR team uses a tool that ranks CVs"
    backend/.venv/bin/python scripts/assess_cli.py --lang it --provider local_mlx --model mlx-community/Qwen2.5-3B-Instruct-4bit "..."
    backend/.venv/bin/python scripts/assess_cli.py --answers role=deployer,human_oversight=human_in_the_loop "..."

Questions are printed and, unless --answers covers them, left unanswered (the
engine then reports its assumptions). Streams the reasoning as it is written.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.chdir(ROOT)
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
os.environ.setdefault("HF_HOME", str(ROOT / "data" / "models"))

from app.corpus.store import CorpusStore  # noqa: E402
from app.pipeline import Pipeline  # noqa: E402


def parse_answers(s: str | None) -> dict[str, object]:
    out: dict[str, object] = {}
    for pair in (s or "").split(","):
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        v = v.strip()
        out[k.strip()] = {"true": True, "false": False}.get(v.lower(), v)
    return out


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("description")
    ap.add_argument("--lang", default="en", choices=["en", "it"])
    ap.add_argument("--provider", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--answers", default=None, help="fact_path=value,… used to answer clarifying questions")
    a = ap.parse_args()
    answers = parse_answers(a.answers)
    store = CorpusStore(ROOT / "data" / "corpus")
    p = Pipeline(store)
    t0 = time.perf_counter()

    def answer(q):  # noqa: ANN001
        v = answers.get(q.fact_path)
        print(f"  ? {q.text[a.lang]}  -> {v if v is not None else '(unanswered)'}")
        return v

    print("Assessing…", flush=True)
    assessment, trace = await p.assess_blocking(a.description, language=a.lang, answer_fn=answer, provider=a.provider, model=a.model)
    if assessment is None:
        print("No result (questions remained unanswered after the maximum rounds).")
        return
    c = assessment.classification
    print(f"\n== {c.tier.upper()} (confidence {c.confidence}, role {c.role}) — {assessment.summary[a.lang] if assessment.summary else ''}")
    print(f"   model {assessment.model.provider}/{assessment.model.model} · {assessment.metrics.latency_ms/1000:.1f} s · "
          f"{assessment.metrics.input_tokens}+{assessment.metrics.output_tokens} tokens · ${assessment.metrics.cost_usd:.4f} · "
          f"{trace['rounds']} question round(s)")
    print("\n-- Reasoning\n" + assessment.reasoning_md)
    print("\n-- Findings")
    for f in c.findings:
        print(f"  {'*' if f.decisive else '-'} {f.title[a.lang]}  [{', '.join(store.label(x, a.lang) for x in f.citations)}]")
    print(f"\n-- Obligations ({len(assessment.obligations)})")
    for o in assessment.obligations:
        print(f"  - {o.title[a.lang]} ({o.role}; from {o.applies_from}) [{', '.join(store.label(x, a.lang) for x in o.citations)}]")
    print(f"\n-- Checklist ({len(assessment.checklist)})")
    for item in assessment.checklist:
        print(f"  [ ] {item.title[a.lang]}")
    if assessment.uncertainties:
        print("\n-- Assumptions and open points")
        for u in assessment.uncertainties:
            print(f"  · {u[a.lang]}")
    print(f"\nLaw as of {assessment.law_as_of} · not legal advice · total {time.perf_counter()-t0:.1f} s")


if __name__ == "__main__":
    asyncio.run(main())
