"""OpenAI-compatible chat/completions provider: the OpenAI API, the NVIDIA catalog and generic servers."""
from __future__ import annotations

import json
import time
from typing import AsyncIterator

import httpx

from .base import JSON_INSTRUCTION, LLMError, LLMProvider, LLMResult, Message, compute_cost, looks_retryable
from .settings import get_settings


def _raise_http(status: int, body: str) -> None:
    raise LLMError(f"HTTP {status}: {body[:300]}", retryable=status in (408, 409, 425, 429) or status >= 500)


class OpenAICompatProvider(LLMProvider):
    def __init__(self, kind: str = "openai_compat", model: str | None = None):
        s = get_settings()
        self.name = kind
        # OpenAI's current models take max_completion_tokens and only the default temperature.
        self.openai_params = kind == "openai_api"
        if kind == "nvidia":
            if not s.nvidia_api_key:
                raise LLMError("No NVIDIA API key: get one at build.nvidia.com, add it in the model picker or set NVIDIA_API_KEY")
            self.base_url, self.key = s.nvidia_base_url, s.nvidia_api_key
            self.json_flag = s.nvidia_json_mode == "1"
            self.model = model or s.nvidia_model
        elif kind == "openai_api":
            if not s.openai_api_key:
                raise LLMError("No OpenAI API key: add one in the model picker or set OPENAI_API_KEY in .env")
            self.base_url, self.key = s.openai_api_base_url, s.openai_api_key
            self.json_flag = True
            self.model = model or s.openai_model
        else:  # generic local server; the key is usually ignored
            self.base_url = s.openai_base_url
            self.key = s.openai_compat_api_key or "not-needed"
            self.json_flag = s.openai_json_mode == "1"
            self.model = model or s.openai_compat_model
        self.base_url = self.base_url.rstrip("/")
        if not self.model:
            raise LLMError(f"no model set for provider {kind!r} (pick one in the model picker or set LLM_MODEL)")
        self.timeout = s.llm_timeout_s

    def _payload(self, messages, temperature, max_tokens, json_mode, stream) -> dict:
        msgs = [dict(m) for m in messages]
        if json_mode:
            for m in msgs:
                if m["role"] == "system":
                    m["content"] += "\n\n" + JSON_INSTRUCTION
                    break
            else:
                msgs.insert(0, {"role": "system", "content": JSON_INSTRUCTION})
        p = {"model": self.model, "messages": msgs, "stream": stream}
        if self.openai_params:
            p["max_completion_tokens"] = max_tokens
        else:
            p["temperature"], p["max_tokens"] = temperature, max_tokens
        if json_mode and self.json_flag:
            p["response_format"] = {"type": "json_object"}
        if stream:
            p["stream_options"] = {"include_usage": True}
        return p

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}

    async def _complete(self, messages, *, temperature, max_tokens, json_mode) -> LLMResult:
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as c:
                r = await c.post(f"{self.base_url}/chat/completions", headers=self._headers(),
                                 json=self._payload(messages, temperature, max_tokens, json_mode, False))
        except httpx.HTTPError as e:
            raise LLMError(f"network error: {e!r}", retryable=True) from e
        if r.status_code >= 400:
            _raise_http(r.status_code, r.text)
        d = r.json()
        try:
            text = d["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as e:
            raise LLMError(f"unexpected response shape: {str(d)[:200]}") from e
        u = d.get("usage") or {}
        it, ot = u.get("prompt_tokens"), u.get("completion_tokens")
        return LLMResult(text, d.get("model") or self.model, self.name, it, ot, compute_cost(it, ot),
                         int((time.perf_counter() - t0) * 1000))

    async def _stream(self, messages, *, temperature, max_tokens) -> AsyncIterator[str | LLMResult]:
        t0 = time.perf_counter()
        parts: list[str] = []
        it = ot = None
        model = self.model
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as c:
                async with c.stream("POST", f"{self.base_url}/chat/completions", headers=self._headers(),
                                    json=self._payload(messages, temperature, max_tokens, False, True)) as r:
                    if r.status_code >= 400:
                        _raise_http(r.status_code, (await r.aread()).decode("utf-8", "replace"))
                    async for line in r.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            ev = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        model = ev.get("model") or model
                        if ev.get("usage"):
                            it, ot = ev["usage"].get("prompt_tokens"), ev["usage"].get("completion_tokens")
                        for ch in ev.get("choices") or []:
                            t = (ch.get("delta") or {}).get("content")
                            if t:
                                parts.append(t)
                                yield t
        except httpx.HTTPError as e:
            raise LLMError(f"network error: {e!r}", retryable=not parts) from e
        yield LLMResult("".join(parts), model, self.name, it, ot, compute_cost(it, ot),
                        int((time.perf_counter() - t0) * 1000))
