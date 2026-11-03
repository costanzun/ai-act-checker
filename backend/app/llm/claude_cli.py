"""Provider using the installed `claude` CLI (subscription login, no API key)."""
from __future__ import annotations

import asyncio
import json
import os
import time
from typing import AsyncIterator

from .base import JSON_INSTRUCTION, LLMError, LLMProvider, LLMResult, Message, looks_retryable, split_system
from .settings import get_settings, resolve_path


def _flatten(msgs: list[Message]) -> str:
    if len(msgs) == 1 and msgs[0]["role"] == "user":
        return msgs[0]["content"]
    label = {"user": "User", "assistant": "Assistant"}
    return "\n\n".join(f"{label.get(m['role'], m['role'])}: {m['content']}" for m in msgs)


class ClaudeCLIProvider(LLMProvider):
    name = "claude_cli"

    def __init__(self, model: str | None = None):
        s = get_settings()
        self.model = model or s.llm_model or "sonnet"
        self.cli = s.claude_cli_path
        self.timeout = s.llm_timeout_s

    def build_argv(self, system: str, *, stream: bool) -> list[str]:
        argv = [self.cli, "-p", "--model", self.model, "--tools", "", "--no-session-persistence",
                "--setting-sources", "", "--strict-mcp-config"]
        if stream:
            argv += ["--output-format", "stream-json", "--include-partial-messages", "--verbose"]
        else:
            argv += ["--output-format", "json"]
        argv += ["--system-prompt", system]
        return argv

    def _prepare(self, messages: list[Message], json_mode: bool) -> tuple[list[str], bytes]:
        system, rest = split_system(messages)
        if json_mode:
            system = (system + "\n\n" if system else "") + JSON_INSTRUCTION
        if not system:
            system = "You are a helpful assistant."
        return system, _flatten(rest).encode("utf-8")

    async def _spawn(self, argv: list[str]) -> asyncio.subprocess.Process:
        cwd = resolve_path(get_settings().claude_cli_cwd)
        cwd.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
        try:
            return await asyncio.create_subprocess_exec(
                *argv, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE, cwd=str(cwd), env=env, limit=16 * 1024 * 1024)
        except FileNotFoundError as e:
            raise LLMError(f"Claude CLI not found at {self.cli!r} (set CLAUDE_CLI_PATH)") from e

    def _to_result(self, obj: dict, t0: float, fallback_text: str = "") -> LLMResult:
        if obj.get("is_error"):
            msg = str(obj.get("result") or obj.get("error") or "claude CLI reported an error")
            raise LLMError(f"claude CLI error: {msg}", retryable=looks_retryable(msg))
        usage = obj.get("usage") or {}
        in_tok = None
        if usage:
            in_tok = (usage.get("input_tokens") or 0) + (usage.get("cache_read_input_tokens") or 0) \
                + (usage.get("cache_creation_input_tokens") or 0)
        mu = obj.get("modelUsage") or {}
        model = next(iter(mu), None) or self.model
        text = obj.get("result")
        if not isinstance(text, str):
            text = fallback_text
        return LLMResult(text=text, model=model, provider=self.name, input_tokens=in_tok,
                         output_tokens=usage.get("output_tokens"), cost_usd=obj.get("total_cost_usd"),
                         latency_ms=int((time.perf_counter() - t0) * 1000), cached=False)

    async def _complete(self, messages, *, temperature, max_tokens, json_mode) -> LLMResult:
        # The CLI exposes neither temperature nor max_tokens; both are ignored.
        t0 = time.perf_counter()
        system, stdin = self._prepare(messages, json_mode)
        proc = await self._spawn(self.build_argv(system, stream=False))
        try:
            out, err = await asyncio.wait_for(proc.communicate(stdin), timeout=self.timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise LLMError(f"claude CLI timed out after {self.timeout}s", retryable=True)
        out_s, err_s = out.decode("utf-8", "replace"), err.decode("utf-8", "replace")
        obj = None
        try:
            obj = json.loads(out_s)
        except json.JSONDecodeError:
            pass
        if isinstance(obj, dict) and obj.get("is_error"):
            return self._to_result(obj, t0)  # raises
        if proc.returncode != 0:
            msg = (err_s or out_s).strip()[:500]
            raise LLMError(f"claude CLI exited {proc.returncode}: {msg}", retryable=looks_retryable(msg))
        if not isinstance(obj, dict):
            raise LLMError(f"claude CLI returned non-JSON output: {out_s[:200]!r}")
        return self._to_result(obj, t0)

    async def _stream(self, messages, *, temperature, max_tokens) -> AsyncIterator[str | LLMResult]:
        t0 = time.perf_counter()
        system, stdin = self._prepare(messages, False)
        proc = await self._spawn(self.build_argv(system, stream=True))
        proc.stdin.write(stdin)
        await proc.stdin.drain()
        proc.stdin.close()
        parts: list[str] = []
        final: dict | None = None
        deadline = time.monotonic() + self.timeout
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise asyncio.TimeoutError
                line = await asyncio.wait_for(proc.stdout.readline(), timeout=remaining)
                if not line:
                    break
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                t = ev.get("type")
                if t == "stream_event":
                    e = ev.get("event") or {}
                    d = e.get("delta") or {}
                    if e.get("type") == "content_block_delta" and d.get("type") == "text_delta" and d.get("text"):
                        parts.append(d["text"])
                        yield d["text"]
                elif t == "result":
                    final = ev
            await asyncio.wait_for(proc.wait(), timeout=10)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise LLMError(f"claude CLI timed out after {self.timeout}s", retryable=not parts)
        except BaseException:
            if proc.returncode is None:
                proc.kill()
            raise
        if final is None:
            err = (await proc.stderr.read()).decode("utf-8", "replace").strip()[:500]
            raise LLMError(f"claude CLI stream ended without result (exit {proc.returncode}): {err}",
                           retryable=looks_retryable(err) and not parts)
        res = self._to_result(final, t0, fallback_text="".join(parts))
        if not res.text:
            res.text = "".join(parts)
        yield res
