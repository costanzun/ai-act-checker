"""Hybrid (vector + FTS) retrieval with optional cross-encoder reranking."""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, TypedDict

from . import PROJECT_ROOT, resolve_path
from .index import LanceIndex

RRF_K = 60


class Hit(TypedDict):
    id: str
    label: str
    snippet: str
    score: float
    type: str
    binding: bool


def _snippet(text: str, n: int = 280) -> str:
    # drop the self-describing header (label — title / [ctx]) added by chunking
    body = text.split("\n", 1)[1] if "\n" in text else text
    if body.startswith("["):
        body = body.split("]\n", 1)[-1]
    body = " ".join(body.split())
    return body if len(body) <= n else body[: n - 1].rsplit(" ", 1)[0] + "…"


class Retriever:
    def __init__(self, store, embedder, index: LanceIndex, reranker=None):
        self.store = store
        self.embedder = embedder
        self.index = index
        self.reranker = reranker

    # ------------------------------------------------------------------ core
    def candidates(self, query: str, lang: str, n: int = 30, types: set[str] | None = None,
                   binding: bool | None = None) -> list[dict]:
        """RRF-fused union of vector and FTS results, de-duplicated by provision id.

        ``binding=True`` restricts to the Regulation itself (articles, annexes, recitals);
        ``binding=False`` to Commission guidance; ``None`` searches both.
        """
        vec = self.embedder.encode_query(query)
        vrows = self.index.search_vector(lang, vec, n, types, binding)
        try:
            frows = self.index.search_fts(lang, query, n, types, binding)
        except Exception:
            frows = []  # FTS unavailable -> vector only
        fused: dict[str, dict] = {}
        for rows in (vrows, frows):
            for rank, r in enumerate(rows):
                cur = fused.get(r["id"])
                if cur is None:
                    cur = fused[r["id"]] = {**r, "rrf": 0.0}
                cur["rrf"] += 1.0 / (RRF_K + rank + 1)
        return sorted(fused.values(), key=lambda r: r["rrf"], reverse=True)[:n]

    def search(self, query: str, lang: str = "en", k: int = 8, candidates: int = 30,
               types: set[str] | None = None, use_reranker: bool = True,
               binding: bool | None = None) -> list[Hit]:
        if not query.strip() or not self.index.has(lang):
            return []
        cands = self.candidates(query, lang, candidates, types, binding)
        if use_reranker and self.reranker is not None and cands:
            ranked = self.reranker.rerank(query, cands, top_k=k)
            score_of = lambda r: r["rerank_score"]  # noqa: E731
        else:
            ranked = cands[:k]
            top = ranked[0]["rrf"] if ranked else 1.0
            score_of = lambda r: r["rrf"] / top if top else 0.0  # noqa: E731
        return [
            Hit(id=r["id"], label=r["label"], snippet=_snippet(r["text"]),
                score=round(float(score_of(r)), 4), type=r["type"], binding=bool(r["binding"]))
            for r in ranked
        ]

    # --------------------------------------------------------------- context
    def get_context(self, ids: list[str], lang: str = "en") -> dict[str, dict[str, str]]:
        """Full texts for prompt grounding: {id: {"label", "text"}} (unknown ids skipped)."""
        out: dict[str, dict[str, str]] = {}
        for i in ids:
            if i in out:
                continue
            try:
                text = self.store.full_text(i, lang)
            except Exception:
                text = ""
            if text:
                out[i] = {"label": self.store.label(i, lang), "text": text}
        return out

    # ------------------------------------------------------------ fact-driven
    def related_for_facts(self, facts: dict, lang: str = "en", k: int = 6, binding: bool | None = True) -> list[Hit]:
        """Compose 2-4 short queries from a FactSheet-like dict and merge hits."""
        queries = facts_to_queries(facts)
        merged: dict[str, Hit] = {}
        for q in queries:
            for h in self.search(q, lang, k=k, candidates=20, binding=binding):
                if h["id"] not in merged or h["score"] > merged[h["id"]]["score"]:
                    merged[h["id"]] = h
        return sorted(merged.values(), key=lambda h: h["score"], reverse=True)[:k]


def _flat(d: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(_flat(v, f"{prefix}{k}."))
    else:
        out[prefix[:-1]] = d
    return out


def facts_to_queries(facts: dict) -> list[str]:
    """Heuristic, deliberately simple: purpose/sector text, Annex III area, and the
    names of boolean flags that are True (plus enum values)."""
    flat = _flat(facts or {})
    queries: list[str] = []
    purpose = " ".join(str(flat[k]) for k in ("purpose", "summary", "description", "system.purpose")
                       if flat.get(k))
    sector = flat.get("sector") or flat.get("domain.sector")
    area = flat.get("annex_iii_area") or flat.get("domain.annex_iii_area")
    if purpose:
        queries.append(purpose[:300])
    if area:
        queries.append(f"high-risk AI systems Annex III {str(area).replace('_', ' ')}")
    if sector and str(sector).lower() not in ("none", "other"):
        queries.append(f"AI system used in {str(sector).replace('_', ' ')} sector obligations")
    flags = [k.split(".")[-1].replace("_", " ") for k, v in flat.items()
             if v is True and k.split(".")[-1] not in ("is_ai_system",)]
    if flags:
        queries.append(" ".join(flags[:6]))
    return queries[:4]


# -------------------------------------------------------------------- factory
_lock = threading.Lock()
_singleton: Retriever | None = None


def _make_store():
    data_dir = resolve_path(os.environ.get("DATA_DIR", ""), "data")
    try:
        from app.corpus.store import CorpusStore  # type: ignore

        return CorpusStore(data_dir)
    except Exception:
        from .chunking import CorpusView

        return _LazyJsonStore(data_dir)


class _LazyJsonStore:
    """Fallback store reading data/corpus/{lang}.json when app.corpus is unavailable."""

    def __init__(self, data_dir: Path):
        self.dir = data_dir
        self._views: dict[str, Any] = {}

    def _v(self, lang):
        from .chunking import CorpusView

        if lang not in self._views:
            self._views[lang] = CorpusView.from_file(self.dir / "corpus" / f"{lang}.json", lang)
        return self._views[lang]

    def full_text(self, id, lang="en"):
        return self._v(lang).full_text(id)

    def label(self, id, lang="en"):
        return self._v(lang).label(id)

    def get(self, id, lang="en"):
        return self._v(lang).get(id)


def get_retriever() -> Retriever:
    global _singleton
    with _lock:
        if _singleton is None:
            from .embeddings import Embedder
            from .rerank import Reranker

            _singleton = Retriever(_make_store(), Embedder(), LanceIndex(), Reranker())
        return _singleton
