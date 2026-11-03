#!/usr/bin/env python
"""Parse the raw EUR-Lex XHTML files into ``data/corpus/{en,it}.json``.

Usage::

    backend/.venv/bin/python scripts/build_corpus.py [--raw-dir DIR] [--out-dir DIR]

Inputs (in ``data/raw``, see ``scripts/fetch_law.py``):

* ``ai-act-consolidated-20260727-{EN,IT}.xhtml``: consolidated text (articles, annexes)
* ``ai-act-original-2024-1689-{EN,IT}.xhtml``: OJ text, used for the 180 recitals only

Exit code is 1 if validation finds a hard error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.corpus.parser import parse_corpus  # noqa: E402

EXPECTED = {"annexes": 14, "recitals": 180}
# 113 numbered articles + 4a, 60a, 75a-75d inserted by Regulation (EU) 2026/1744
EXPECTED_ARTICLES = [str(n) for n in range(1, 114)] + ["4a", "60a", "75a", "75b", "75c", "75d"]


def validate(corpus: dict) -> tuple[list[str], list[str]]:
    """Return (errors, notes) for one language's corpus."""
    errs: list[str] = []
    notes: list[str] = []
    provs = corpus["provisions"]
    ids = [p["id"] for p in provs]
    by_id = {p["id"]: p for p in provs}
    if len(ids) != len(by_id):
        errs.append("duplicate IDs present")
    orders = [p["order"] for p in provs]
    if orders != sorted(orders) or len(set(orders)) != len(orders):
        errs.append("order is not strictly increasing")
    for p in provs:
        if p["parent_id"] and p["parent_id"] not in by_id:
            errs.append(f"{p['id']}: missing parent {p['parent_id']}")
        for c in p["children"]:
            if c not in by_id or by_id[c]["parent_id"] != p["id"]:
                errs.append(f"{p['id']}: bad child {c}")
        deleted = (p["amendment"] or {}).get("kind") == "deleted"
        if not p["text"] and not deleted:
            errs.append(f"{p['id']}: empty text")
        if re.search(r"[▼►◄]", (p["text"] or "") + (p["body"] or "") + (p["text_after"] or "")):
            errs.append(f"{p['id']}: amendment glyph left in text")
    arts = [p["id"][4:] for p in provs if p["type"] == "article"]
    if sorted(arts) != sorted(EXPECTED_ARTICLES):
        errs.append(f"article set differs from expected: missing={sorted(set(EXPECTED_ARTICLES)-set(arts))} extra={sorted(set(arts)-set(EXPECTED_ARTICLES))}")
    recs = sorted(p["recital"] for p in provs if p["type"] == "recital")
    if recs != list(range(1, 181)):
        errs.append("recitals are not exactly 1..180")
    c = corpus["meta"]["counts"]
    for k, v in EXPECTED.items():
        if c[k] != v:
            errs.append(f"count {k}={c[k]} (expected {v})")
    notes.append(f"{sum(1 for p in provs if p['amendment'])} provisions carry amendment metadata; "
                 f"{sum(1 for p in provs if (p['amendment'] or {}).get('kind') == 'deleted')} deleted")
    notes.append("restarted child lists (suffix -N): " + ", ".join(i for i in ids if re.search(r"-\d+$", i)))
    return errs, notes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "data" / "corpus")
    ap.add_argument("--retrieved-at", default=date.today().isoformat())
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    corpora: dict[str, dict] = {}
    hard = 0
    for lang in ("en", "it"):
        up = lang.upper()
        corpus, warns = parse_corpus(
            args.raw_dir / f"ai-act-consolidated-20260727-{up}.xhtml",
            args.raw_dir / f"ai-act-original-2024-1689-{up}.xhtml",
            lang,
            args.retrieved_at,
        )
        errs, notes = validate(corpus)
        out = args.out_dir / f"{lang}.json"
        with out.open("w", encoding="utf-8") as f:
            f.write('{"meta": ' + json.dumps(corpus["meta"], ensure_ascii=False) + ',\n"provisions": [\n')
            f.write(",\n".join(json.dumps(p, ensure_ascii=False) for p in corpus["provisions"]))
            f.write("\n]}\n")
        corpora[lang] = corpus
        print(f"[{lang}] wrote {out} counts={corpus['meta']['counts']}")
        for n in notes:
            print(f"[{lang}] note: {n}")
        for w in warns + errs:
            print(f"[{lang}] PROBLEM: {w}")
        hard += len(errs) + len(warns)

    en = {p["id"] for p in corpora["en"]["provisions"]}
    it = {p["id"] for p in corpora["it"]["provisions"]}
    if en == it:
        print(f"ID sets identical across languages ({len(en)} IDs)")
    else:
        hard += 1
        print(f"ID SET DIFF only-en={sorted(en - it)[:50]} only-it={sorted(it - en)[:50]}")
    print("VALIDATION " + ("FAILED" if hard else "OK"))
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
