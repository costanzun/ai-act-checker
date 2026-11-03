"""Provider ABC, result types, shared caching/limits/logging wrapper."""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Literal, TypedDict

from .cache import CacheEntry, LLMCache, make_key
from .limits import get_semaphore, retry
from .settings import get_settings, resolve_path

log = logging.getLogger("ai_act.llm")


class Message(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMError(RuntimeError):
    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


@dataclass
class LLMResult:
    text: str
    model: str
    provider: str
    input_tokens: int | None
    output_tokens: int | None
    cost_usd: float | None
    latency_ms: int
    cached: bool = False


_RETRYABLE_HINTS = ("rate limit", "rate_limit", "overloaded", "429", "529", "503", "502", "504", "timeout",
                    "timed out", "network", "connection", "temporarily", "try again", "econnreset", "capacity")


def looks_retryable(msg: str) -> bool:
    m = msg.lower()
    return any(h in m for h in _RETRYABLE_HINTS)


def compute_cost(input_tokens: int | None, output_tokens: int | None) -> float | None:
    s = get_settings()
    if s.llm_price_input_per_m is None or s.llm_price_output_per_m is None or input_tokens is None or output_tokens is None:
        return None
    return (input_tokens * s.llm_price_input_per_m + output_tokens * s.llm_price_output_per_m) / 1e6


_cache: LLMCache | None = None


def get_cache() -> LLMCache:
    global _cache
    s = get_settings()
    if _cache is None or _cache.enabled != s.cache_enabled or str(_cache.path) != str(resolve_path(s.llm_cache_path)):
        _cache = LLMCache()
    return _cache


class LLMProvider(ABC):
    name: str = "base"
    model: str = ""

    # ---- to implement -----------------------------------------------------
    @abstractmethod
    async def _complete(self, messages: list[Message], *, temperature: float, max_tokens: int,
                        json_mode: bool) -> LLMResult: ...

    @abstractmethod
    def _stream(self, messages: list[Message], *, temperature: float,
                max_tokens: int) -> AsyncIterator[str | LLMResult]: ...

    # ---- public API -------------------------------------------------------
    def _log(self, r: LLMResult) -> None:
        log.info("llm provider=%s model=%s in=%s out=%s ms=%d cached=%s",
                 self.name, r.model, r.input_tokens, r.output_tokens, r.latency_ms, r.cached)

    def _lookup(self, key: str, t0: float) -> LLMResult | None:
        hit = get_cache().get(key)
        if not hit:
            return None
        return LLMResult(hit.text, hit.model or self.model, self.name, hit.input_tokens, hit.output_tokens,
                         hit.cost_usd, int((time.perf_counter() - t0) * 1000), True)

    async def complete(self, messages: list[Message], *, temperature: float = 0.0, max_tokens: int = 2048,
                       json_mode: bool = False) -> LLMResult:
        t0 = time.perf_counter()
        key = make_key(self.name, self.model, messages, temperature, max_tokens, json_mode)
        hit = self._lookup(key, t0)
        if hit:
            self._log(hit)
            return hit
        log.debug("prompt: %r", messages)

        async def call() -> LLMResult:
            async with get_semaphore():
                return await self._complete(messages, temperature=temperature, max_tokens=max_tokens,
                                            json_mode=json_mode)

        res = await retry(call)
        get_cache().put(key, CacheEntry(res.text, res.model, res.input_tokens, res.output_tokens, res.cost_usd))
        self._log(res)
        return res

    async def stream(self, messages: list[Message], *, temperature: float = 0.0,
                     max_tokens: int = 2048) -> AsyncIterator[str | LLMResult]:
        t0 = time.perf_counter()
        key = make_key(self.name, self.model, messages, temperature, max_tokens, False)
        hit = self._lookup(key, t0)
        if hit:
            self._log(hit)
            yield hit.text
            yield hit
            return
        log.debug("prompt: %r", messages)
        # Retry only while nothing has been yielded yet.
        attempts, backoff = 3, (1, 3, 9)
        import asyncio

        for i in range(attempts):
            emitted = False
            try:
                async with get_semaphore():
                    async for item in self._stream(messages, temperature=temperature, max_tokens=max_tokens):
                        if isinstance(item, LLMResult):
                            get_cache().put(key, CacheEntry(item.text, item.model, item.input_tokens,
                                                            item.output_tokens, item.cost_usd))
                            self._log(item)
                        else:
                            emitted = True
                        yield item
                return
            except LLMError as e:
                if emitted or not e.retryable or i == attempts - 1:
                    raise
                log.warning("LLM transient stream error (%d/%d): %s", i + 1, attempts, e)
                await asyncio.sleep(backoff[i])


JSON_INSTRUCTION = (
    "Respond with a single valid JSON object and nothing else: no prose before or after, "
    "no markdown code fences, no comments."
)


def split_system(messages: list[Message]) -> tuple[str, list[Message]]:
    sys_parts = [m["content"] for m in messages if m["role"] == "system"]
    return "\n\n".join(sys_parts), [m for m in messages if m["role"] != "system"]
