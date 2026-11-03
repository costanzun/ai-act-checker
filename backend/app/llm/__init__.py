"""LLM provider layer. See docs/CONTRACTS.md section 6."""
from __future__ import annotations

from .base import LLMError, LLMProvider, LLMResult, Message
from .json_utils import JSONParseError, parse_json_object
from .settings import get_settings

PROVIDERS = ("claude_cli", "nvidia", "local_mlx", "anthropic_api", "openai_compat")


def get_provider(name: str | None = None, model: str | None = None) -> LLMProvider:
    s = get_settings()
    name = (name or s.llm_provider or "claude_cli").strip()
    if name == "claude_cli":
        from .claude_cli import ClaudeCLIProvider
        return ClaudeCLIProvider(model)
    if name in ("nvidia", "openai_compat"):
        from .openai_compat import OpenAICompatProvider
        return OpenAICompatProvider(name, model)
    if name == "local_mlx":
        from .mlx_local import MLXProvider
        return MLXProvider(model)
    if name == "anthropic_api":
        from .anthropic_api import AnthropicAPIProvider
        return AnthropicAPIProvider(model)
    raise LLMError(f"unknown LLM provider {name!r}; valid: {', '.join(PROVIDERS)}")


__all__ = ["get_provider", "LLMProvider", "LLMResult", "Message", "LLMError", "parse_json_object",
           "JSONParseError", "PROVIDERS"]
