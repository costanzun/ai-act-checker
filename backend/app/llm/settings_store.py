"""The model connection chosen in the app, saved to ``data/llm_settings.json``.

The file is gitignored, written with mode 600 and layered over ``.env`` by ``get_settings()``.
API keys are write-only through the API: reads return a masked hint, never the key.
"""
from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .settings import PROJECT_ROOT

FILE = PROJECT_ROOT / "data" / "llm_settings.json"


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    label: str
    kind: str  # "subscription" | "api_key" | "local"
    blurb: str
    model_field: str
    default_model: str = ""
    key_field: str | None = None
    key_url: str | None = None
    model_hint: str = ""
    suggestions: tuple[str, ...] = field(default_factory=tuple)


PROVIDERS: list[ProviderSpec] = [
    ProviderSpec("claude_cli", "Claude subscription", "subscription",
                 "Uses Claude Code signed in on this computer (Pro or Max plan). No key needed.",
                 model_field="claude_cli_model", default_model="sonnet", model_hint="sonnet, opus or haiku",
                 suggestions=("sonnet", "opus", "haiku")),
    ProviderSpec("codex_cli", "ChatGPT subscription", "subscription",
                 "Uses OpenAI's Codex CLI signed in with your ChatGPT account. No key needed.",
                 model_field="codex_model", model_hint="empty = Codex default"),
    ProviderSpec("anthropic_api", "Anthropic API key", "api_key",
                 "Pay per use with a key from the Claude Console.",
                 model_field="anthropic_model", default_model="claude-sonnet-5-5",
                 key_field="anthropic_api_key", key_url="https://console.anthropic.com/settings/keys",
                 model_hint="a model id", suggestions=("claude-sonnet-5-5", "claude-opus-5-5")),
    ProviderSpec("openai_api", "OpenAI API key", "api_key",
                 "Pay per use with a key from the OpenAI platform.",
                 model_field="openai_model", key_field="openai_api_key",
                 key_url="https://platform.openai.com/api-keys", model_hint="a model id from your dashboard"),
    ProviderSpec("nvidia", "NVIDIA API key", "api_key",
                 "Free developer key for open models (Llama, Nemotron).",
                 model_field="nvidia_model", key_field="nvidia_api_key",
                 key_url="https://build.nvidia.com/settings/api-keys",
                 model_hint="e.g. meta/llama-3.3-70b-instruct"),
    ProviderSpec("local_mlx", "Local model (offline)", "local",
                 "Runs a Qwen model on this Mac with MLX. Free and private, slower and less sharp.",
                 model_field="mlx_model", model_hint="an MLX model id"),
]
BY_ID = {p.id: p for p in PROVIDERS}

# Only these settings attributes can be written from the API.
WRITABLE = {"llm_provider"} | {p.model_field for p in PROVIDERS} | {p.key_field for p in PROVIDERS if p.key_field}


def load_overrides(path: Path | None = None) -> dict[str, str]:
    try:
        data = json.loads((path or FILE).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if k in WRITABLE and isinstance(v, str)}


def save_overrides(update: dict[str, str], path: Path | None = None) -> dict[str, str]:
    """Merge ``update`` into the saved overrides. An empty string removes that override."""
    bad = set(update) - WRITABLE
    if bad:
        raise ValueError(f"not writable: {', '.join(sorted(bad))}")
    p = path or FILE
    data = load_overrides(p)
    for k, v in update.items():
        if v.strip() == "":
            data.pop(k, None)
        else:
            data[k] = v.strip()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(json.dumps(data, indent=2))
    os.chmod(tmp, 0o600)
    tmp.replace(p)
    return data


def mask(key: str) -> str | None:
    if not key:
        return None
    return f"{key[:3]}…{key[-4:]}" if len(key) > 10 else "…" + key[-2:]


def binary(path: str) -> str | None:
    """Resolved CLI path, or None (a dangling symlink counts as missing). Never runs it."""
    found = shutil.which(path) or (path if Path(path).expanduser().is_file() else None)
    return found if found and os.access(found, os.X_OK) else None


def model_of(settings: Any, spec: ProviderSpec) -> str:
    return getattr(settings, spec.model_field, "") or spec.default_model


def describe(settings: Any) -> dict[str, Any]:
    """Public view of every option. Never includes a full key."""
    out = []
    for p in PROVIDERS:
        key = getattr(settings, p.key_field, "") if p.key_field else ""
        model = model_of(settings, p)
        if p.id == "claude_cli":
            ok = bool(binary(settings.claude_cli_path))
            ready, status = ok, "Claude Code found" if ok else "Claude Code is not installed"
        elif p.id == "codex_cli":
            ok = bool(binary(settings.codex_cli_path))
            ready, status = ok, "Codex CLI found" if ok else "Codex CLI is not installed"
        elif p.kind == "api_key":
            ready = bool(key and model)
            status = "No key yet" if not key else ("Key saved" if model else "Key saved, pick a model")
        else:
            ready, status = True, "Runs on this Mac"
        out.append({
            "id": p.id, "label": p.label, "kind": p.kind, "blurb": p.blurb, "key_url": p.key_url,
            "needs_key": p.key_field is not None, "has_key": bool(key), "key_hint": mask(key),
            "model": model, "model_hint": p.model_hint, "suggestions": list(p.suggestions),
            "ready": ready, "status": status, "active": settings.llm_provider == p.id,
        })
    return {"active": settings.llm_provider, "providers": out}
