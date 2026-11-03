"""Retrieval layer: chunking, embeddings, LanceDB hybrid index, reranking.

Heavy imports (torch, sentence-transformers, lancedb) are deferred; importing
this package is cheap.
"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def resolve_path(p: str | os.PathLike, default: str | None = None) -> Path:
    """Resolve an env-style path; relative paths are relative to the project root."""
    path = Path(p or default or ".")
    return path if path.is_absolute() else PROJECT_ROOT / path


def get_retriever():
    from .search import get_retriever as _g

    return _g()


__all__ = ["PROJECT_ROOT", "resolve_path", "get_retriever"]
