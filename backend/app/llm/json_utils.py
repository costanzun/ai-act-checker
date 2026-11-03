"""Tolerant JSON-object extraction from LLM output."""
from __future__ import annotations

import json
import re


class JSONParseError(ValueError):
    def __init__(self, message: str, snippet: str = ""):
        super().__init__(f"{message}: {snippet[:300]!r}")
        self.snippet = snippet


_FENCE = re.compile(r"```(?:json|JSON)?\s*\n?(.*?)```", re.S)
_SMART = {"“": '"', "”": '"', "„": '"', "‘": "'", "’": "'"}


def _outermost_object(s: str) -> str | None:
    """Return the first balanced {...} (string-aware), or the tail from the first '{' if unbalanced."""
    start = s.find("{")
    if start < 0:
        return None
    depth, in_str, esc = 0, False, False
    for i in range(start, len(s)):
        c = s[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    return s[start:]


def _strip_trailing_commas(s: str) -> str:
    out, in_str, esc = [], False, False
    n = len(s)
    for i, c in enumerate(s):
        if in_str:
            out.append(c)
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == ",":
            j = i + 1
            while j < n and s[j].isspace():
                j += 1
            if j < n and s[j] in "}]":
                continue
        out.append(c)
    return "".join(out)


def _fix_smart_quotes(s: str) -> str:
    """Replace smart double quotes used as JSON delimiters (outside strings) with ASCII quotes.

    A string opened by a smart quote is closed by the next smart quote; inside ASCII strings
    smart quotes are left alone.
    """
    out, mode, esc = [], None, False  # mode: None | "ascii" | "smart"
    for c in s:
        if mode == "ascii":
            out.append(c)
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                mode = None
            continue
        if mode == "smart":
            if c in ("\u201c", "\u201d", "\u201e"):
                out.append('"')
                mode = None
            elif c == '"':
                out.append('\\"')
            else:
                out.append(c)
            continue
        if c in ("\u201c", "\u201d", "\u201e"):
            out.append('"')
            mode = "smart"
        else:
            out.append(c)
            if c == '"':
                mode = "ascii"
    return "".join(out)


def parse_json_object(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise JSONParseError("empty LLM output", str(text))
    candidates = [text]
    m = _FENCE.search(text)
    if m:
        candidates.insert(0, m.group(1))
    last_err: Exception | None = None
    for cand in candidates:
        obj = _outermost_object(cand)
        if obj is None:
            continue
        for fix in (lambda x: x, _strip_trailing_commas, lambda x: _strip_trailing_commas(_fix_smart_quotes(x))):
            try:
                val = json.loads(fix(obj))
            except json.JSONDecodeError as e:
                last_err = e
                continue
            if isinstance(val, dict):
                return val
    raise JSONParseError(f"no valid JSON object found ({last_err})" if last_err else "no JSON object found", text)
