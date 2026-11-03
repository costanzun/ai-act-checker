#!/usr/bin/env python
"""Build the LanceDB retrieval index from data/corpus/{en,it}.json (+ data/guidance/*.json).

Usage: backend/.venv/bin/python scripts/build_index.py [--lang en|it|all] [--rebuild]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.example")  # defaults only; real .env wins (load_dotenv doesn't override)

from app.retrieval.chunking import CorpusView, chunk_corpus  # noqa: E402
from app.retrieval.embeddings import Embedder  # noqa: E402
from app.retrieval.index import LanceIndex  # noqa: E402


def collect(lang: str, corpus_file: str | None = None) -> list[dict]:
    chunks: list[dict] = []
    f = Path(corpus_file) if corpus_file else ROOT / "data" / "corpus" / f"{lang}.json"
    if f.exists():
        v = CorpusView.from_file(f, lang)
        c = chunk_corpus(v, lang, binding=True)
        print(f"  corpus/{lang}.json: {len(v.provisions)} provisions -> {len(c)} chunks")
        chunks += c
    else:
        print(f"  corpus/{lang}.json missing")
    for g in sorted((ROOT / "data" / "guidance").glob("*.json")) if not corpus_file else []:
        meta = json.loads(g.read_text(encoding="utf-8")).get("meta", {})
        if meta.get("language", "en") != lang:
            continue
        v = CorpusView.from_file(g, lang)
        c = chunk_corpus(v, lang, binding=False)
        print(f"  guidance/{g.name}: {len(v.provisions)} provisions -> {len(c)} chunks (non-binding)")
        chunks += c
    return chunks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="all", choices=["en", "it", "all"])
    ap.add_argument("--rebuild", action="store_true", help="rebuild even if the table already exists")
    ap.add_argument("--corpus-file", default=None, help="override corpus JSON (single --lang only; skips guidance)")
    ap.add_argument("--batch-size", type=int, default=16)
    a = ap.parse_args()

    langs = ["en", "it"] if a.lang == "all" else [a.lang]
    index = LanceIndex()
    emb = Embedder()
    for lang in langs:
        print(f"[{lang}]")
        if index.has(lang) and not a.rebuild:
            print(f"  table exists ({index.count(lang)} rows); use --rebuild to recreate")
            continue
        chunks = collect(lang, a.corpus_file)
        if not chunks:
            print("  nothing to index")
            continue
        t = time.time()
        info = index.build(lang, chunks, emb, batch_size=a.batch_size, show_progress=True)
        print(f"  indexed {info['rows']} chunks (dim {info['dim']}, fts={info['fts']}) in {time.time()-t:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
