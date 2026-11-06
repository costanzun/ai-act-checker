"""Keep the model choice saved from the app (data/llm_settings.json) out of every test."""
from __future__ import annotations

import pytest

from app.llm import settings, settings_store


@pytest.fixture(autouse=True)
def _no_saved_llm_choice(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_store, "FILE", tmp_path / "llm_settings.json")
    settings.get_settings.cache_clear()
    yield
    settings.get_settings.cache_clear()
