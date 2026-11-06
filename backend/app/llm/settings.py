"""Settings (pydantic-settings). Reads .env from project root and backend/; real env vars win."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


def resolve_path(p: str | Path) -> Path:
    """Relative paths are relative to the project root."""
    p = Path(p).expanduser()
    return p if p.is_absolute() else PROJECT_ROOT / p


class LLMSettings(BaseSettings):
    # later files override earlier ones: backend/.env beats root .env; env vars beat both
    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "claude_cli"
    # Legacy shared model: applies to the provider named in LLM_PROVIDER (see get_settings).
    llm_model: str = ""
    llm_max_concurrency: int = 2
    llm_cache: str = "1"
    llm_cache_path: str = "data/cache/llm.sqlite"
    llm_timeout_s: float = 180.0
    llm_price_input_per_m: float | None = None
    llm_price_output_per_m: float | None = None

    # Per-provider models; empty means the provider's default.
    claude_cli_path: str = "claude"
    claude_cli_cwd: str = "data/.claude-cli-cwd"
    claude_cli_model: str = ""

    # ChatGPT subscription through OpenAI's Codex CLI (`codex login`); empty model = Codex default.
    codex_cli_path: str = "codex"
    codex_model: str = ""

    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_json_mode: str = "0"
    nvidia_model: str = "meta/llama-3.3-70b-instruct"

    # Real OpenAI API (provider openai_api).
    openai_api_key: str = ""
    openai_api_base_url: str = "https://api.openai.com/v1"
    openai_model: str = ""

    # Any OpenAI-compatible server, e.g. llama-server or vLLM (provider openai_compat).
    openai_base_url: str = "http://localhost:8080/v1"
    openai_compat_api_key: str = ""
    openai_compat_model: str = ""
    openai_json_mode: str = "0"

    mlx_model: str = "mlx-community/Qwen2.5-14B-Instruct-4bit"
    mlx_small_model: str = "mlx-community/Qwen2.5-3B-Instruct-4bit"

    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_model: str = "claude-sonnet-5-5"

    hf_home: str = "data/models"

    @property
    def cache_enabled(self) -> bool:
        return self.llm_cache.strip().lower() not in ("0", "false", "no", "off", "")


# Which settings field holds the model of each provider.
MODEL_FIELD = {
    "claude_cli": "claude_cli_model",
    "codex_cli": "codex_model",
    "anthropic_api": "anthropic_model",
    "openai_api": "openai_model",
    "nvidia": "nvidia_model",
    "openai_compat": "openai_compat_model",
    "local_mlx": "mlx_model",
}


@lru_cache
def get_settings() -> LLMSettings:
    """.env, then the choice saved from the app (data/llm_settings.json), which wins."""
    from .settings_store import load_overrides

    s = LLMSettings()
    # Backward compatibility: LLM_MODEL is the model of the provider named in LLM_PROVIDER,
    # unless that provider's own model variable was set explicitly.
    field = MODEL_FIELD.get(s.llm_provider.strip())
    if s.llm_model and field and field not in s.model_fields_set:
        s = s.model_copy(update={field: s.llm_model})
    # OPENAI_API_KEY=not-needed was the placeholder for local OpenAI-compatible servers.
    if s.openai_api_key.strip().lower() == "not-needed":
        s = s.model_copy(update={"openai_api_key": ""})
    overrides = load_overrides()
    if overrides:
        s = s.model_copy(update=overrides)
    return s
