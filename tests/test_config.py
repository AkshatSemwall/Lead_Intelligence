import pytest

from backend.config import Settings


def test_settings_requires_gemini_key_when_provider_is_gemini() -> None:
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        Settings(_env_file=None, gemini_api_key="", llm_provider="gemini")


def test_settings_requires_openai_key_when_provider_is_openai() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        Settings(_env_file=None, gemini_api_key="", openai_api_key="", llm_provider="openai")
