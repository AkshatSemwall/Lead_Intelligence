"""
LLM client abstraction.
Supports Gemini (default), OpenAI, and Anthropic via provider flag in config.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _make_gemini(settings: Any):
    import google.generativeai as genai  # type: ignore

    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(settings.gemini_model)


class LLMClient:
    """Thin wrapper that lets agents call generate() without caring which LLM is used."""

    def __init__(self, settings: Any | None = None) -> None:
        from backend.config import get_settings

        self._settings = settings or get_settings()
        self._provider = self._settings.llm_provider
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        if self._provider == "gemini":
            self._client = _make_gemini(self._settings)
        elif self._provider == "openai":
            from openai import AsyncOpenAI  # type: ignore

            self._client = AsyncOpenAI(api_key=self._settings.openai_api_key)
        elif self._provider == "claude":
            import anthropic  # type: ignore

            self._client = anthropic.AsyncAnthropic(api_key=self._settings.anthropic_api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self._provider}")

        return self._client

    async def generate(self, prompt: str, temperature: float = 0.3) -> str:
        """Generate text from a prompt. Returns the text response."""
        client = self._get_client()

        if self._provider == "gemini":
            import asyncio
            import functools

            model = client
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                functools.partial(
                    model.generate_content,
                    prompt,
                    generation_config={"temperature": temperature},
                ),
            )
            return response.text

        elif self._provider == "openai":
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            return response.choices[0].message.content or ""

        elif self._provider == "claude":
            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8096,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            return response.content[0].text

        raise ValueError(f"Unsupported provider: {self._provider}")


# Module-level singleton factory
_llm_instance: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMClient()
    return _llm_instance
