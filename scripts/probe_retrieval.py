#!/usr/bin/env python
"""Run backend/tests/probes_retrieval.yaml against the real index; report hit@5 with/without reranker.

Usage: backend/.venv/bin/python scripts/probe_retrieval.py [--lang en] [--index-dir DIR] [--only-existing PATH_TO_CORPUS_JSON]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.example")

from app.retrieval.chunking import CorpusView  # noqa: E402
from app.retrieval.embeddings import Embedder  # noqa: E402
from app.retrieval.index import LanceIndex  # noqa: E402
from app.retrieval.rerank import Reranker  # noqa: E402
from app.retrieval.search import Retriever  # noqa: E402


def ok(expect: str, got: str) -> bool:
    return got == expect or got.startswith(expect + ".")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en")
    ap.add_argument("--index-dir", default=None)
    ap.add_argument("--corpus", default=None, help="corpus JSON used for the store / to skip probes whose target is absent")
    ap.add_argument("--all-sources", action="store_true", help="also search non-binding guidance (default: binding provisions only)")
    a = ap.parse_args()
    corpus = Path(a.corpus or ROOT / "data" / "corpus" / f"{a.lang}.json")
    view = CorpusView.from_file(corpus, a.lang)
    probes = yaml.safe_load((ROOT / "backend/tests/probes_retrieval.yaml").read_text())
    probes = [p for p in probes if any(ok(p["expect"], i) for i in view.by_id)]
    r = Retriever(view, Embedder(), LanceIndex(a.index_dir), Reranker())
    r.search("warm up", a.lang, k=2)  # load models before timing
    summary = {}
    for rr in (False, True):
        hits5 = hits1 = 0
        t = time.time()
        for p in probes:
            res = r.search(p["q"], a.lang, k=5, use_reranker=rr, binding=None if a.all_sources else True)
            ids = [h["id"] for h in res]
            pos = next((i for i, x in enumerate(ids) if ok(p["expect"], x)), None)
            hits5 += pos is not None
            hits1 += pos == 0
            print(f"[{'rerank' if rr else 'hybrid'}] {'OK ' if pos is not None else 'MISS'} @{pos}  {p['q'][:55]:55s} -> {p['expect']}  got {ids[:3]}")
        dt = (time.time() - t) / len(probes)
        summary[rr] = (hits5, hits1, len(probes), dt)
    for rr, (h5, h1, n, dt) in summary.items():
        print(f"reranker={rr}: hit@5 {h5}/{n}  hit@1 {h1}/{n}  latency {dt*1000:.0f} ms/query")
    return 0


if __name__ == "__main__":
    sys.exit(main())
