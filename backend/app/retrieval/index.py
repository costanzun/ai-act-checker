"""LanceDB index: one table per language, vector column + FTS on text."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa

from . import resolve_path

_LANG_NAMES = {"en": "English", "it": "Italian"}


def table_name(lang: str) -> str:
    return f"provisions_{lang}"


def make_schema(dim: int) -> pa.Schema:
    return pa.schema([
        pa.field("id", pa.string()),
        pa.field("chunk_ix", pa.int32()),
        pa.field("text", pa.string()),
        pa.field("label", pa.string()),
        pa.field("title", pa.string()),
        pa.field("type", pa.string()),
        pa.field("article", pa.string()),
        pa.field("annex", pa.string()),
        pa.field("lang", pa.string()),
        pa.field("binding", pa.bool_()),
        pa.field("vector", pa.list_(pa.float32(), dim)),
    ])


def _fts_query(q: str) -> str:
    """Strip punctuation that the FTS query parser may choke on."""
    return " ".join(re.findall(r"\w+", q, flags=re.UNICODE))


class LanceIndex:
    def __init__(self, index_dir: str | os.PathLike | None = None):
        import lancedb

        self.path = resolve_path(index_dir or os.environ.get("INDEX_DIR", ""), "data/index")
        self.path.mkdir(parents=True, exist_ok=True)
        self.db = lancedb.connect(str(self.path))
        self.fts_ok: dict[str, bool] = {}

    # -- introspection -------------------------------------------------------
    def has(self, lang: str) -> bool:
        return table_name(lang) in self._names()

    def _names(self) -> list[str]:
        res = self.db.list_tables() if hasattr(self.db, "list_tables") else self.db.table_names()
        return list(getattr(res, "tables", res))

    def count(self, lang: str) -> int:
        return self.db.open_table(table_name(lang)).count_rows() if self.has(lang) else 0

    # -- build ---------------------------------------------------------------
    def build(self, lang: str, chunks: list[dict], embedder, batch_size: int = 16,
              show_progress: bool = False) -> dict[str, Any]:
        """Idempotent: overwrites the table for `lang` with `chunks`."""
        dim = embedder.dim
        vecs = embedder.encode([c["text"] for c in chunks], batch_size=batch_size,
                               show_progress=show_progress) if chunks else np.zeros((0, dim), np.float32)
        rows = [{**c, "vector": v.tolist()} for c, v in zip(chunks, vecs)]
        tbl = self.db.create_table(table_name(lang), data=rows, schema=make_schema(dim), mode="overwrite")
        fts = True
        try:
            from lancedb.index import FTS

            tbl.create_index("text", config=FTS(language=_LANG_NAMES.get(lang, "English"), stem=True,
                                                remove_stop_words=True, ascii_folding=True), replace=True)
        except Exception:  # older lancedb: deprecated helper
            try:
                tbl.create_fts_index("text", replace=True)
            except Exception:
                fts = False
        self.fts_ok[lang] = fts
        return {"lang": lang, "rows": tbl.count_rows(), "dim": dim, "fts": fts}

    # -- search --------------------------------------------------------------
    def _where(self, types: set[str] | None, binding: bool | None = None) -> str | None:
        clauses: list[str] = []
        if types:
            clauses.append("type IN (" + ", ".join("'" + t.replace("'", "") + "'" for t in sorted(types)) + ")")
        if binding is not None:
            clauses.append(f"binding = {'true' if binding else 'false'}")
        return " AND ".join(clauses) if clauses else None

    def search_vector(self, lang: str, vec: np.ndarray, n: int, types: set[str] | None = None,
                      binding: bool | None = None) -> list[dict]:
        tbl = self.db.open_table(table_name(lang))
        q = tbl.search(vec.astype(np.float32), vector_column_name="vector").metric("cosine")
        w = self._where(types, binding)
        if w:
            q = q.where(w, prefilter=True)
        rows = q.limit(n).to_list()
        for r in rows:
            r["vscore"] = 1.0 - float(r.get("_distance", 1.0))
            r.pop("vector", None)
        return rows

    def search_fts(self, lang: str, query: str, n: int, types: set[str] | None = None,
                   binding: bool | None = None) -> list[dict]:
        tbl = self.db.open_table(table_name(lang))
        qs = _fts_query(query)
        if not qs:
            return []
        q = tbl.search(qs, query_type="fts")
        w = self._where(types, binding)
        if w:
            q = q.where(w, prefilter=True)
        rows = q.limit(n).to_list()
        for r in rows:
            r["fscore"] = float(r.get("_score", 0.0))
            r.pop("vector", None)
        return rows
