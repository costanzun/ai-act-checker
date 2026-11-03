"""Cross-encoder reranker wrapper (lazy)."""
from __future__ import annotations

import os

from .embeddings import pick_device, setup_hf_env


class Reranker:
    def __init__(self, model_name: str | None = None, device: str | None = None, max_length: int = 512,
                 batch_size: int = 16):
        self.model_name = model_name or os.environ.get("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
        self.device = device
        self.max_length = max_length
        self.batch_size = batch_size
        self._model = None

    def _load(self):
        if self._model is None:
            setup_hf_env(self.model_name)
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name, device=self.device or pick_device(),
                                       max_length=self.max_length)
        return self._model

    def score(self, query: str, texts: list[str]) -> list[float]:
        if not texts:
            return []
        s = self._load().predict([(query, t) for t in texts], batch_size=self.batch_size,
                                 show_progress_bar=False)
        return [float(x) for x in s]

    def rerank(self, query: str, candidates: list[dict], top_k: int = 8, text_key: str = "text") -> list[dict]:
        """Return the top_k candidates (copies) sorted by cross-encoder score, with
        `rerank_score` set."""
        scores = self.score(query, [c[text_key] for c in candidates])
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [{**c, "rerank_score": s} for c, s in ranked]
