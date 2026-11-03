"""Retrieval tests; no model downloads (FakeEmbedder / FakeReranker injected)."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pytest

from app.retrieval.chunking import CorpusView, chunk_corpus, split_text
from app.retrieval.index import LanceIndex
from app.retrieval.search import Retriever, facts_to_queries

FIXTURE = Path(__file__).parent / "fixtures" / "mini_corpus_en.json"


class FakeEmbedder:
    """Deterministic hashed bag-of-words vectors (normalised)."""

    dim = 128

    def encode(self, texts, batch_size=16, show_progress=False):
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            for w in re.findall(r"\w+", t.lower()):
                h = int(hashlib.md5(w.encode()).hexdigest(), 16)
                out[i, h % self.dim] += 1.0
            n = np.linalg.norm(out[i])
            if n:
                out[i] /= n
        return out

    def encode_query(self, text):
        return self.encode([text])[0]


class FakeReranker:
    """Scores by word overlap between query and candidate text."""

    def rerank(self, query, candidates, top_k=8, text_key="text"):
        q = set(re.findall(r"\w+", query.lower()))
        sc = [(c, len(q & set(re.findall(r"\w+", c[text_key].lower()))) / (len(q) or 1)) for c in candidates]
        sc.sort(key=lambda x: x[1], reverse=True)
        return [{**c, "rerank_score": s} for c, s in sc[:top_k]]


@pytest.fixture(scope="module")
def view():
    return CorpusView.from_file(FIXTURE, "en")


@pytest.fixture(scope="module")
def chunks(view):
    return chunk_corpus(view, "en")


@pytest.fixture(scope="module")
def retriever(chunks, view, tmp_path_factory):
    idx = LanceIndex(tmp_path_factory.mktemp("index"))
    emb = FakeEmbedder()
    info = idx.build("en", chunks, emb)
    assert info["rows"] == len(chunks)
    return Retriever(view, emb, idx, FakeReranker())


def test_fixture_shape():
    d = json.loads(FIXTURE.read_text())
    ids = {p["id"] for p in d["provisions"]}
    assert len(ids) == len(d["provisions"]) >= 25
    for must in ["art:5.1.f", "art:6.2", "art:6.3", "art:50.1", "annex:III.4.a", "annex:III.1.c", "rec:57", "art:26.7"]:
        assert must in ids
    for p in d["provisions"]:
        for c in p["children"]:
            assert c in ids


def test_chunks_leaves_only_and_self_describing(chunks):
    ids = {c["id"] for c in chunks}
    assert "art:5.1.f" in ids and "art:5" not in ids and "art:5.1" not in ids  # parents are not chunks
    c = next(c for c in chunks if c["id"] == "art:5.1.f")
    assert c["text"].startswith("Art. 5(1)(f) — Prohibited AI practices\n")
    assert "The following AI practices shall be prohibited" in c["text"]  # ancestor intro
    assert "infer emotions" in c["text"]
    assert c["type"] == "point" and c["article"] == "5" and c["lang"] == "en" and c["binding"] is True
    a = next(c for c in chunks if c["id"] == "annex:III.4.a")
    assert a["annex"] == "III" and a["article"] == ""
    r = next(c for c in chunks if c["id"] == "rec:57")
    assert r["text"].startswith("Recital 57\n")


def test_chunk_cap_and_split(chunks):
    assert all(len(c["text"]) <= 1200 for c in chunks)
    long = [c for c in chunks if c["id"] == "art:6.3"]
    assert len(long) >= 1
    assert [c["chunk_ix"] for c in long] == list(range(len(long)))
    parts = split_text("Sentence one is here. " * 100, 300)
    assert all(len(p) <= 300 for p in parts) and len(parts) > 1


def test_guidance_not_binding(view):
    g = CorpusView([{"id": "guid:x.1", "type": "guidance", "label": "G §1", "parent_id": None, "children": [],
                     "title": "Guidelines", "text": "Some guidance text.", "article": None, "annex": None}], "en", binding=False)
    ch = chunk_corpus(g)
    assert ch and ch[0]["binding"] is False


def test_index_build_idempotent(retriever, chunks):
    n = retriever.index.count("en")
    retriever.index.build("en", chunks, retriever.embedder)
    assert retriever.index.count("en") == n == len(chunks)


def test_emotion_workplace(retriever):
    hits = retriever.search("emotion recognition at the workplace", "en", k=5)
    assert "art:5.1.f" in [h["id"] for h in hits]


def test_cv_screening(retriever):
    hits = retriever.search("screening CVs of job applicants", "en", k=5)
    assert "annex:III.4.a" in [h["id"] for h in hits]


def test_no_reranker_and_types_and_dedupe(retriever):
    hits = retriever.search("chatbot must tell users they are interacting with an AI system", "en", k=5,
                            use_reranker=False)
    assert hits[0]["id"] == "art:50.1"
    ids = [h["id"] for h in hits]
    assert len(ids) == len(set(ids))
    assert set(hits[0]) == {"id", "label", "snippet", "score", "type", "binding"}
    only_rec = retriever.search("workers recruitment", "en", k=5, types={"recital"})
    assert only_rec and all(h["type"] == "recital" for h in only_rec)


def test_fts_failure_falls_back_to_vector(retriever, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("no fts")

    monkeypatch.setattr(retriever.index, "search_fts", boom)
    hits = retriever.search("emotion recognition at the workplace", "en", k=5)
    assert hits


def test_unknown_lang_and_empty(retriever):
    assert retriever.search("x", "it") == []
    assert retriever.search("  ", "en") == []


def test_get_context(retriever):
    ctx = retriever.get_context(["art:5.1.f", "art:6", "nope"], "en")
    assert "nope" not in ctx
    assert ctx["art:5.1.f"]["label"] == "Art. 5(1)(f)"
    assert "infer emotions" in ctx["art:5.1.f"]["text"]
    assert "AI systems referred to in Annex III" in ctx["art:6"]["text"]  # full_text assembles children


def test_related_for_facts(retriever):
    facts = {"sector": "employment", "annex_iii_area": "employment", "flags": {"emotion_recognition": True}}
    qs = facts_to_queries(facts)
    assert 2 <= len(qs) <= 4
    hits = retriever.related_for_facts(facts, "en", k=6)
    assert hits and len({h["id"] for h in hits}) == len(hits)
