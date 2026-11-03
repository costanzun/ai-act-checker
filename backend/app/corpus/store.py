"""Read-only, in-memory access to the parsed legal corpus (CONTRACTS section 3).

The corpus JSON files (``data/corpus/en.json`` / ``it.json``) are loaded lazily,
once per language, into dictionaries keyed by provision ID; all lookups are
O(1). No network access.
"""

from __future__ import annotations

import json
import re
import threading
from collections.abc import Iterator
from pathlib import Path

from .models import CorpusMeta, Provision

LANGS = ("en", "it")
_EURLEX_BASE = "https://eur-lex.europa.eu/legal-content/{lang}/TXT/?uri=CELEX:{celex}"
_ORIGINAL_CELEX = "32024R1689"


def default_data_dir() -> Path:
    """``<repo>/data/corpus`` (this file lives in ``<repo>/backend/app/corpus``)."""
    return Path(__file__).resolve().parents[3] / "data" / "corpus"


class _Lang:
    """One loaded language."""

    def __init__(self, path: Path) -> None:
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.meta = CorpusMeta.model_validate(raw["meta"])
        self.ordered: list[Provision] = [Provision.model_validate(p) for p in raw["provisions"]]
        self.by_id: dict[str, Provision] = {p.id: p for p in self.ordered}


class CorpusStore:
    """Lazy-loading store for the EN and IT corpora."""

    def __init__(self, data_dir: Path | str | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else default_data_dir()
        self._langs: dict[str, _Lang] = {}
        self._lock = threading.Lock()

    # -- loading ------------------------------------------------------------ #
    def _lang(self, lang: str) -> _Lang:
        if lang not in LANGS:
            raise ValueError(f"unsupported language {lang!r}; expected one of {LANGS}")
        loaded = self._langs.get(lang)
        if loaded is None:
            with self._lock:
                loaded = self._langs.get(lang)
                if loaded is None:
                    loaded = _Lang(self.data_dir / f"{lang}.json")
                    self._langs[lang] = loaded
        return loaded

    # -- API -------------------------------------------------------------------- #
    def get(self, id: str, lang: str = "en") -> Provision | None:  # noqa: A002
        """Return the provision or ``None`` if unknown."""
        return self._lang(lang).by_id.get(id)

    def exists(self, id: str) -> bool:  # noqa: A002
        """True if the ID resolves in the English corpus (IDs are language-neutral)."""
        return id in self._lang("en").by_id

    def label(self, id: str, lang: str = "en") -> str:  # noqa: A002
        """Display label (``Art. 6(2)`` / ``Art. 6, par. 2``); the ID itself if unknown."""
        p = self.get(id, lang)
        return p.label if p else id

    def meta(self, lang: str = "en") -> CorpusMeta:
        """Corpus metadata for a language."""
        return self._lang(lang).meta

    def iter(self, lang: str = "en", types: set[str] | None = None) -> Iterator[Provision]:
        """Iterate provisions in document order, optionally filtered by ``type``."""
        for p in self._lang(lang).ordered:
            if types is None or p.type in types:
                yield p

    def children(self, id: str, lang: str = "en") -> list[Provision]:  # noqa: A002
        """Direct children of a provision, in order."""
        by_id = self._lang(lang).by_id
        p = by_id.get(id)
        return [by_id[c] for c in p.children if c in by_id] if p else []

    def breadcrumb(self, id: str, lang: str = "en") -> list[Provision]:  # noqa: A002
        """Ancestors from the root down to (and including) the provision."""
        by_id = self._lang(lang).by_id
        chain: list[Provision] = []
        p = by_id.get(id)
        while p is not None:
            chain.append(p)
            p = by_id.get(p.parent_id) if p.parent_id else None
        return chain[::-1]

    def full_text(self, id: str, lang: str = "en") -> str:  # noqa: A002
        """Assemble a provision with all its descendants, one item per line.

        Paragraphs are prefixed ``1.``, points ``(a)``; sub-points are indented.
        Deleted provisions are omitted.
        """
        by_id = self._lang(lang).by_id
        root = by_id.get(id)
        if root is None:
            return ""
        lines: list[str] = []

        def render(p: Provision, depth: int, top: bool) -> None:
            if p.amendment and p.amendment.kind == "deleted":
                return
            prefix = "" if top else _prefix(p)
            indent = "" if top or depth <= 1 else "  " * (depth - 1)
            own = [p.text] if p.text else []
            if p.body:
                own.append(p.body)
            joined = "\n".join(own)
            if joined:
                first, *rest = joined.split("\n")
                lines.append(f"{indent}{prefix}{first}")
                lines.extend(f"{indent}{r}" for r in rest)
            for cid in p.children:
                c = by_id.get(cid)
                if c is not None:
                    render(c, depth + 1, False)
            if p.text_after:
                lines.extend(f"{indent}{r}" for r in p.text_after.split("\n"))

        render(root, 0, True)
        return "\n".join(lines)

    def eurlex_url(self, id: str, lang: str = "en") -> str:  # noqa: A002
        """Deep link to EUR-Lex (consolidated text; recitals link to the OJ text)."""
        lg = lang.upper()
        p = self.get(id, "en")
        celex = self._lang("en").meta.celex
        anchor = ""
        if p is not None:
            if p.type == "recital" and p.recital:
                celex, anchor = _ORIGINAL_CELEX, f"#rct_{p.recital}"
            elif p.article is not None:
                anchor = f"#art_{p.article}"
            elif p.annex:
                anchor = f"#anx_{p.annex}"
        return _EURLEX_BASE.format(lang=lg, celex=celex) + anchor


_TOKEN_RE = re.compile(r"-\d+$")


def _prefix(p: Provision) -> str:
    """Printed label of a node inside its parent (``1. `` / ``(a) ``)."""
    tok = _TOKEN_RE.sub("", p.id.rsplit(".", 1)[-1])
    if p.type == "paragraph":
        return f"{tok}. "
    if p.type == "annex_point":
        m = re.fullmatch(r"(?:[A-Z]\.)?(\d+(?:\.\d+)+)", p.point or "")
        if m:  # dotted numbering such as Annex VII, 3.1
            return f"{m.group(1)}. "
        if len(tok) == 1 and tok.isalpha() and tok.isupper():
            return f"Section {tok}. "
        if tok.isdigit() and (p.parent_id or "").startswith("annex:") and "." not in (p.parent_id or "")[6:]:
            return f"{tok}. "
        return f"({tok}) " if not tok.isdigit() else f"{tok}. "
    return f"({tok}) "
