"""ChatGPT subscription through OpenAI's Codex CLI, run headless.

Command (prompt on **stdin**)::

    codex exec --skip-git-repo-check --sandbox read-only --ephemeral \\
        --output-last-message <file> [--model M] -

Codex has no system-prompt flag, so the system text leads the prompt. It runs in an empty temp
folder so no project files are in reach. Codex does not stream here: ``_stream`` yields the whole
answer at once.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
import time
from collections.abc import AsyncIterator
from pathlib import Path

from .base import JSON_INSTRUCTION, LLMError, LLMProvider, LLMResult, Message, looks_retryable, split_system
from .settings import get_settings
from .settings_store import binary

_AUTH = ("not logged in", "please log in", "codex login", "unauthorized", "401")
_LIMIT = ("usage limit",)


def build_command(binary_path: str, out_file: Path, model: str) -> list[str]:
    cmd = [binary_path, "exec", "--skip-git-repo-check", "--sandbox", "read-only", "--ephemeral",
           "--output-last-message", str(out_file)]
    if model:
        cmd += ["--model", model]
    return cmd + ["-"]


def build_stdin(messages: list[Message], json_mode: bool) -> str:
    system, rest = split_system(messages)
    if json_mode:
        system = (system + "\n\n" if system else "") + JSON_INSTRUCTION
    label = {"user": "User", "assistant": "Assistant"}
    if len(rest) == 1 and rest[0]["role"] == "user":
        convo = rest[0]["content"]
    else:
        convo = "\n\n".join(f"{label.get(m['role'], m['role'])}: {m['content']}" for m in rest)
    parts = [system, convo, "Do not run commands or edit files. Answer directly."]
    return "\n\n".join(p for p in parts if p)


def check_exit(code: int, text: str, log: str) -> None:
    """Raise LLMError for a failed run; sign-in problems and usage limits are not retried."""
    if code == 0 and text.strip():
        return
    blob = log.strip()[-400:] or f"exit {code}, empty answer"
    low = blob.lower()
    if any(m in low for m in _AUTH):
        raise LLMError("Codex is not signed in: run `codex login`", retryable=False)
    retryable = looks_retryable(blob) and not any(m in low for m in _LIMIT)
    raise LLMError(f"codex exit {code}: {blob}", retryable=retryable)


class CodexCLIProvider(LLMProvider):
    name = "codex_cli"

    def __init__(self, model: str | None = None):
        s = get_settings()
        found = binary(s.codex_cli_path)
        if not found:
            raise LLMError("Codex CLI not found: install it (npm install -g @openai/codex) and run `codex login`")
        self.cli = found
        self._model = model or s.codex_model
        self.model = self._model or "codex-default"
        self.timeout = s.llm_timeout_s

    async def _complete(self, messages, *, temperature, max_tokens, json_mode) -> LLMResult:
        # Codex exposes neither temperature nor max_tokens; both are ignored.
        t0 = time.perf_counter()
        work = Path(tempfile.mkdtemp(prefix="ai-act-codex-"))
        out_file = work / "answer.txt"
        try:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *build_command(self.cli, out_file, self._model),
                    stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE, cwd=str(work), env=dict(os.environ))
            except OSError as e:
                raise LLMError(f"cannot start Codex CLI: {e}") from e
            try:
                out, err = await asyncio.wait_for(
                    proc.communicate(build_stdin(messages, json_mode).encode("utf-8")), self.timeout)
            except TimeoutError:
                proc.kill()
                await proc.wait()
                raise LLMError(f"codex timed out after {self.timeout}s", retryable=True)
            text = out_file.read_text() if out_file.exists() else ""
            check_exit(proc.returncode or 0, text, (err or out).decode("utf-8", "replace"))
            return LLMResult(text.strip(), self.model, self.name, None, None, None,
                             int((time.perf_counter() - t0) * 1000))
        finally:
            shutil.rmtree(work, ignore_errors=True)

    async def _stream(self, messages, *, temperature, max_tokens) -> AsyncIterator[str | LLMResult]:
        res = await self._complete(messages, temperature=temperature, max_tokens=max_tokens, json_mode=False)
        yield res.text
        yield res
