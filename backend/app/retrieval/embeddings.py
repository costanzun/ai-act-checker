"""Local sentence-embedding wrapper (lazy, normalised, MPS-aware)."""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from . import resolve_path


def setup_hf_env(model_name: str | None = None) -> Path:
    """Make HF_HOME absolute (relative -> project root) before huggingface_hub is
    imported, and go offline when the model is already cached."""
    hf_home = resolve_path(os.environ.get("HF_HOME", ""), "data/models")
    os.environ["HF_HOME"] = str(hf_home)
    if model_name and (hf_home / "hub" / ("models--" + model_name.replace("/", "--"))).exists():
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
    return hf_home


def pick_device() -> str:
    import torch

    return "mps" if torch.backends.mps.is_available() else "cpu"


class Embedder:
    def __init__(self, model_name: str | None = None, device: str | None = None, max_seq_length: int = 512):
        self.model_name = model_name or os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")
        self.device = device
        self.max_seq_length = max_seq_length
        self._model = None
        self._dim: int | None = None

    def _load(self):
        if self._model is None:
            setup_hf_env(self.model_name)
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device=self.device or pick_device())
            self._model.max_seq_length = self.max_seq_length
            getter = getattr(self._model, "get_embedding_dimension", None) or self._model.get_sentence_embedding_dimension
            self._dim = int(getter())
        return self._model

    @property
    def dim(self) -> int:
        if self._dim is None:
            self._load()
        return self._dim  # type: ignore[return-value]

    def encode(self, texts: list[str], batch_size: int = 16, show_progress: bool = False) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        v = self._load().encode(
            texts, batch_size=batch_size, normalize_embeddings=True,
            convert_to_numpy=True, show_progress_bar=show_progress,
        )
        return v.astype(np.float32)

    def encode_query(self, text: str) -> np.ndarray:
        return self.encode([text])[0]
