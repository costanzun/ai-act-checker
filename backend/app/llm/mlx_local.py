"""In-process MLX provider (Apple Silicon)."""
from __future__ import annotations

import asyncio
import threading
import time
from typing import AsyncIterator

from .base import JSON_INSTRUCTION, LLMError, LLMProvider, LLMResult, Message
from .settings import get_settings, resolve_path

_MODELS: dict[str, tuple] = {}
_LOAD_LOCK = threading.Lock()
_GEN_LOCK = threading.Lock()  # MLX generation is not safe to run concurrently


def _load(model_id: str):
    import os

    os.environ.setdefault("HF_HOME", str(resolve_path(get_settings().hf_home)))
    with _LOAD_LOCK:
        if model_id not in _MODELS:
            try:
                from mlx_lm import load
            except ImportError as e:
                raise LLMError("mlx-lm is not installed (Apple Silicon only)") from e
            try:
                _MODELS[model_id] = load(model_id)[:2]
            except Exception as e:  # missing weights, offline, ...
                raise LLMError(f"could not load MLX model {model_id!r}: {e}. "
                               "Run scripts/download_models.py --llm-only") from e
        return _MODELS[model_id]


class MLXProvider(LLMProvider):
    name = "local_mlx"

    def __init__(self, model: str | None = None):
        s = get_settings()
        self.model = model or s.mlx_model

    def _prompt(self, tok, messages: list[Message], json_mode: bool):
        msgs = [dict(m) for m in messages]
        if json_mode:
            for m in msgs:
                if m["role"] == "system":
                    m["content"] += "\n\n" + JSON_INSTRUCTION
                    break
            else:
                msgs.insert(0, {"role": "system", "content": JSON_INSTRUCTION})
        return tok.apply_chat_template(msgs, add_generation_prompt=True)

    def _generate_sync(self, messages, temperature, max_tokens, json_mode, on_text=None):
        from mlx_lm import stream_generate
        from mlx_lm.sample_utils import make_sampler

        model, tok = _load(self.model)
        prompt = self._prompt(tok, messages, json_mode)
        in_tokens = len(prompt) if isinstance(prompt, list) else len(tok.encode(prompt))
        sampler = make_sampler(temp=temperature)
        parts: list[str] = []
        out_tokens = 0
        with _GEN_LOCK:
            for resp in stream_generate(model, tok, prompt, max_tokens=max_tokens, sampler=sampler):
                parts.append(resp.text)
                out_tokens = getattr(resp, "generation_tokens", out_tokens + 1)
                if on_text and resp.text:
                    on_text(resp.text)
        return "".join(parts), in_tokens, out_tokens

    async def _complete(self, messages, *, temperature, max_tokens, json_mode) -> LLMResult:
        t0 = time.perf_counter()
        text, it, ot = await asyncio.to_thread(self._generate_sync, messages, temperature, max_tokens, json_mode)
        return LLMResult(text, self.model, self.name, it, ot, 0.0, int((time.perf_counter() - t0) * 1000))

    async def _stream(self, messages, *, temperature, max_tokens) -> AsyncIterator[str | LLMResult]:
        t0 = time.perf_counter()
        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()

        def work():
            try:
                r = self._generate_sync(messages, temperature, max_tokens, False,
                                        on_text=lambda t: loop.call_soon_threadsafe(q.put_nowait, t))
                loop.call_soon_threadsafe(q.put_nowait, r)
            except BaseException as e:  # noqa: BLE001
                loop.call_soon_threadsafe(q.put_nowait, e)

        fut = asyncio.create_task(asyncio.to_thread(work))
        try:
            while True:
                item = await q.get()
                if isinstance(item, BaseException):
                    raise item if isinstance(item, LLMError) else LLMError(f"MLX generation failed: {item}")
                if isinstance(item, tuple):
                    text, it, ot = item
                    yield LLMResult(text, self.model, self.name, it, ot, 0.0, int((time.perf_counter() - t0) * 1000))
                    return
                yield item
        finally:
            await fut
