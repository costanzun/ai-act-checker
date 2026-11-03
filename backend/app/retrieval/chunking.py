"""Turn corpus provisions into self-describing retrieval chunks."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterator, TypedDict

MAX_CHARS = 1200


class Chunk(TypedDict):
    id: str
    chunk_ix: int
    text: str  # label + title + body; what gets embedded / indexed
    label: str
    title: str
    type: str
    article: str
    annex: str
    lang: str
    binding: bool


class CorpusView:
    """Minimal read-only view over a corpus JSON (store-compatible subset:
    get / full_text / label / iter). Used for the build script and as a fallback
    when `app.corpus.CorpusStore` is unavailable."""

    def __init__(self, provisions: list[dict], lang: str = "en", binding: bool = True):
        self.lang = lang
        self.binding = binding
        self.by_id = {p["id"]: p for p in provisions}
        self.provisions = provisions

    @classmethod
    def from_file(cls, path: Path | str, lang: str | None = None) -> "CorpusView":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        meta = data.get("meta", {})
        return cls(
            data["provisions"],
            lang or meta.get("language", "en"),
            binding=meta.get("binding", True) is not False,
        )

    def get(self, id: str, lang: str = "en") -> dict | None:
        return self.by_id.get(id)

    def label(self, id: str, lang: str = "en") -> str:
        p = self.by_id.get(id)
        return p["label"] if p else id

    def exists(self, id: str) -> bool:
        return id in self.by_id

    def iter(self, lang: str = "en", types: set[str] | None = None) -> Iterator[dict]:
        for p in self.provisions:
            if types is None or p["type"] in types:
                yield p

    def full_text(self, id: str, lang: str = "en") -> str:
        p = self.by_id.get(id)
        if not p:
            return ""
        parts = [p.get("text") or ""]
        for cid in p.get("children") or []:
            c = self.full_text(cid)
            if c:
                parts.append(c)
        return "\n".join(x for x in parts if x)


_SENT = re.compile(r"(?<=[.;:!?])\s+(?=[A-Z0-9(‘“\"'])")


def split_text(text: str, limit: int) -> list[str]:
    """Split on sentence boundaries into pieces <= limit chars (hard-wrap on spaces
    as a last resort)."""
    if len(text) <= limit:
        return [text]
    out: list[str] = []
    cur = ""
    for s in _SENT.split(text):
        while len(s) > limit:  # no boundary: wrap on whitespace
            cut = s.rfind(" ", 0, limit)
            cut = cut if cut > limit // 2 else limit
            if cur:
                out.append(cur)
                cur = ""
            out.append(s[:cut].strip())
            s = s[cut:].strip()
        if cur and len(cur) + 1 + len(s) > limit:
            out.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        out.append(cur)
    return out


def _ancestor_context(view: CorpusView, p: dict, max_chars: int = 240) -> str:
    """Intro text of the parent chain for points, e.g. 'The following AI practices
    shall be prohibited:' — makes a bare point self-describing."""
    if p["type"] not in ("point", "annex_point"):
        return ""
    bits: list[str] = []
    pid = p.get("parent_id")
    while pid and pid in view.by_id:
        par = view.by_id[pid]
        if par["type"] in ("article", "annex"):
            break
        if par.get("text"):
            bits.append(par["text"].strip())
        pid = par.get("parent_id")
    ctx = " > ".join(reversed(bits))
    return ctx[:max_chars]


def chunk_provision(view: CorpusView, p: dict, lang: str, binding: bool, max_chars: int = MAX_CHARS) -> list[Chunk]:
    body = view.full_text(p["id"]).strip()
    if not body:
        return []
    title = p.get("title") or ""
    head = p["label"] + (f" — {title}" if title else "")
    ctx = _ancestor_context(view, p)
    prefix = head + "\n" + (f"[{ctx}]\n" if ctx else "")
    budget = max(200, max_chars - len(prefix))
    pieces = split_text(body, budget)
    return [
        Chunk(
            id=p["id"],
            chunk_ix=i,
            text=prefix + piece,
            label=p["label"],
            title=title,
            type=p["type"],
            article=str(p["article"]) if p.get("article") is not None else "",
            annex=p.get("annex") or "",
            lang=lang,
            binding=binding,
        )
        for i, piece in enumerate(pieces)
    ]


def is_leaf(p: dict) -> bool:
    return not p.get("children")


def chunk_corpus(view: CorpusView, lang: str | None = None, binding: bool | None = None,
                 max_chars: int = MAX_CHARS) -> list[Chunk]:
    lang = lang or view.lang
    binding = view.binding if binding is None else binding
    out: list[Chunk] = []
    for p in view.provisions:
        if not is_leaf(p):
            continue
        if (p.get("amendment") or {}).get("kind") == "deleted":
            continue
        b = binding and p["type"] != "guidance"
        out.extend(chunk_provision(view, p, lang, b, max_chars))
    return out
