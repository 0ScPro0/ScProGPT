"""Tests for `core.ai.models`."""

import pytest

from core.ai.models import load_models  # type: ignore


class TestLoadModels:
    def test_load_openai(self):
        data = load_models("openai")
        assert "default" in data
        assert "supported" in data
        assert isinstance(data["supported"], list)
        assert len(data["supported"]) > 0

    def test_load_openrouter(self):
        data = load_models("openrouter")
        assert "default" in data
        assert "supported" in data

    def test_load_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_models("nonexistent_provider")
