"""Direct Anthropic Messages API provider (httpx, no SDK)."""
from __future__ import annotations

import json
import time
from typing import AsyncIterator

import httpx

from .base import JSON_INSTRUCTION, LLMError, LLMProvider, LLMResult, Message, compute_cost, split_system
from .settings import get_settings


class AnthropicAPIProvider(LLMProvider):
    name = "anthropic_api"

    def __init__(self, model: str | None = None):
        s = get_settings()
        if not s.anthropic_api_key:
            raise LLMError("No Anthropic API key: add one in the model picker or set ANTHROPIC_API_KEY in .env")
        self.key = s.anthropic_api_key
        self.url = s.anthropic_base_url.rstrip("/") + "/v1/messages"
        self.model = model or s.anthropic_model or "claude-sonnet-5-5"
        self.timeout = s.llm_timeout_s

    def _payload(self, messages, temperature, max_tokens, json_mode, stream) -> dict:
        system, rest = split_system(messages)
        if json_mode:
            system = (system + "\n\n" if system else "") + JSON_INSTRUCTION
        p = {"model": self.model, "max_tokens": max_tokens, "temperature": temperature,
             "messages": [{"role": m["role"], "content": m["content"]} for m in rest], "stream": stream}
        if system:
            p["system"] = system
        return p

    def _headers(self) -> dict:
        return {"x-api-key": self.key, "anthropic-version": "2023-06-01", "content-type": "application/json"}

    @staticmethod
    def _err(status: int, body: str):
        raise LLMError(f"Anthropic API HTTP {status}: {body[:300]}", retryable=status in (408, 429, 529) or status >= 500)

    async def _complete(self, messages, *, temperature, max_tokens, json_mode) -> LLMResult:
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as c:
                r = await c.post(self.url, headers=self._headers(),
                                 json=self._payload(messages, temperature, max_tokens, json_mode, False))
        except httpx.HTTPError as e:
            raise LLMError(f"network error: {e!r}", retryable=True) from e
        if r.status_code >= 400:
            self._err(r.status_code, r.text)
        d = r.json()
        text = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
        u = d.get("usage") or {}
        it, ot = u.get("input_tokens"), u.get("output_tokens")
        return LLMResult(text, d.get("model") or self.model, self.name, it, ot, compute_cost(it, ot),
                         int((time.perf_counter() - t0) * 1000))

    async def _stream(self, messages, *, temperature, max_tokens) -> AsyncIterator[str | LLMResult]:
        t0 = time.perf_counter()
        parts: list[str] = []
        it = ot = None
        model = self.model
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as c:
                async with c.stream("POST", self.url, headers=self._headers(),
                                    json=self._payload(messages, temperature, max_tokens, False, True)) as r:
                    if r.status_code >= 400:
                        self._err(r.status_code, (await r.aread()).decode("utf-8", "replace"))
                    async for line in r.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        try:
                            ev = json.loads(line[5:].strip())
                        except json.JSONDecodeError:
                            continue
                        t = ev.get("type")
                        if t == "message_start":
                            m = ev.get("message") or {}
                            model = m.get("model") or model
                            it = (m.get("usage") or {}).get("input_tokens")
                        elif t == "content_block_delta" and (ev.get("delta") or {}).get("type") == "text_delta":
                            parts.append(ev["delta"]["text"])
                            yield ev["delta"]["text"]
                        elif t == "message_delta":
                            ot = (ev.get("usage") or {}).get("output_tokens", ot)
                        elif t == "error":
                            msg = json.dumps(ev.get("error"))
                            raise LLMError(f"Anthropic stream error: {msg}",
                                           retryable=(not parts) and "overloaded" in msg)
        except httpx.HTTPError as e:
            raise LLMError(f"network error: {e!r}", retryable=not parts) from e
        yield LLMResult("".join(parts), model, self.name, it, ot, compute_cost(it, ot),
                        int((time.perf_counter() - t0) * 1000))
