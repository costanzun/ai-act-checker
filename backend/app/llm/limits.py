"""Process-wide concurrency limit and retry helper."""
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, TypeVar

from .settings import get_settings

log = logging.getLogger("ai_act.llm")
T = TypeVar("T")

_semaphores: dict[asyncio.AbstractEventLoop, asyncio.Semaphore] = {}


def get_semaphore() -> asyncio.Semaphore:
    """One semaphore per running event loop (sized by LLM_MAX_CONCURRENCY)."""
    loop = asyncio.get_running_loop()
    sem = _semaphores.get(loop)
    if sem is None:
        _semaphores.clear()  # drop semaphores of dead loops (tests)
        sem = _semaphores[loop] = asyncio.Semaphore(max(1, get_settings().llm_max_concurrency))
    return sem


async def retry(fn: Callable[[], Awaitable[T]], attempts: int = 3, backoff: tuple[float, ...] = (1, 3, 9)) -> T:
    from .base import LLMError

    for i in range(attempts):
        try:
            return await fn()
        except LLMError as e:
            if not e.retryable or i == attempts - 1:
                raise
            delay = backoff[min(i, len(backoff) - 1)]
            log.warning("LLM transient error (attempt %d/%d): %s; retrying in %ss", i + 1, attempts, e, delay)
            await asyncio.sleep(delay)
    raise AssertionError("unreachable")
