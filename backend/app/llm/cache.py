"""SQLite response cache keyed on the call parameters."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from dataclasses import dataclass

from .settings import get_settings, resolve_path


@dataclass
class CacheEntry:
    text: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    cost_usd: float | None


def make_key(provider: str, model: str, messages, temperature: float, max_tokens: int, json_mode: bool) -> str:
    payload = json.dumps(
        [provider, model, messages, temperature, max_tokens, json_mode],
        sort_keys=True, ensure_ascii=False, default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class LLMCache:
    def __init__(self, path: str | None = None, enabled: bool | None = None):
        s = get_settings()
        self.enabled = s.cache_enabled if enabled is None else enabled
        self.path = resolve_path(path or s.llm_cache_path) if not str(path or "").startswith(":") else path
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None

    def _db(self) -> sqlite3.Connection:
        if self._conn is None:
            if not str(self.path).startswith(":"):
                self.path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS llm_cache (key TEXT PRIMARY KEY, text TEXT NOT NULL, model TEXT,"
                " input_tokens INTEGER, output_tokens INTEGER, cost_usd REAL, created_at REAL)"
            )
            self._conn.commit()
        return self._conn

    def get(self, key: str) -> CacheEntry | None:
        if not self.enabled:
            return None
        with self._lock:
            row = self._db().execute(
                "SELECT text, model, input_tokens, output_tokens, cost_usd FROM llm_cache WHERE key=?", (key,)
            ).fetchone()
        return CacheEntry(*row) if row else None

    def put(self, key: str, e: CacheEntry) -> None:
        if not self.enabled:
            return
        with self._lock:
            db = self._db()
            db.execute(
                "INSERT OR REPLACE INTO llm_cache VALUES (?,?,?,?,?,?,?)",
                (key, e.text, e.model, e.input_tokens, e.output_tokens, e.cost_usd, time.time()),
            )
            db.commit()

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
