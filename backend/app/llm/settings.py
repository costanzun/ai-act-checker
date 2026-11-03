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
    llm_model: str = ""
    llm_max_concurrency: int = 2
    llm_cache: str = "1"
    llm_cache_path: str = "data/cache/llm.sqlite"
    llm_timeout_s: float = 180.0
    llm_price_input_per_m: float | None = None
    llm_price_output_per_m: float | None = None

    claude_cli_path: str = "claude"
    claude_cli_cwd: str = "data/.claude-cli-cwd"

    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_json_mode: str = "0"

    openai_base_url: str = "http://localhost:8080/v1"
    openai_api_key: str = "not-needed"
    openai_json_mode: str = "0"

    mlx_model: str = "mlx-community/Qwen2.5-14B-Instruct-4bit"
    mlx_small_model: str = "mlx-community/Qwen2.5-3B-Instruct-4bit"

    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://api.anthropic.com"

    hf_home: str = "data/models"

    @property
    def cache_enabled(self) -> bool:
        return self.llm_cache.strip().lower() not in ("0", "false", "no", "off", "")


@lru_cache
def get_settings() -> LLMSettings:
    return LLMSettings()
