"""LLM client abstraction with deterministic fallbacks."""
from __future__ import annotations

import json
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
            if not self._settings.gemini_api_key:
                raise RuntimeError("GEMINI_API_KEY is not configured")
            self._client = _make_gemini(self._settings)
        elif self._provider == "openai":
            if not self._settings.openai_api_key:
                raise RuntimeError("OPENAI_API_KEY is not configured")
            from openai import AsyncOpenAI  # type: ignore

            self._client = AsyncOpenAI(api_key=self._settings.openai_api_key)
        elif self._provider == "claude":
            if not self._settings.anthropic_api_key:
                raise RuntimeError("ANTHROPIC_API_KEY is not configured")
            import anthropic  # type: ignore

            self._client = anthropic.AsyncAnthropic(api_key=self._settings.anthropic_api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self._provider}")

        return self._client

    def _fallback_response(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "markdown report" in prompt_lower or "executive summary" in prompt_lower:
            return "# Business Audit Report\n\n## Executive Summary\nThis report was generated using the built-in fallback content generator because the configured LLM provider was unavailable. The workflow completed with graceful degradation and captured the essential structure for downstream steps.\n\n## Company Overview\nThe company profile is based on the available workflow inputs and fallback heuristics to ensure the report remains usable.\n\n## Recommendations\n- Validate the company profile with additional research data.\n- Prioritise automation opportunities that reduce manual operational effort.\n- Prepare a concise 90-day plan for implementation."

        if "json object" in prompt_lower or "return only valid json" in prompt_lower or "extract" in prompt_lower:
            return json.dumps({
                "company_name": "Fallback Company",
                "website_url": "https://example.com",
                "industry": "Unknown",
                "description": "Fallback analysis generated because the LLM provider was unavailable.",
                "services": ["Business consulting"],
                "technology_stack": ["Fallback mode"],
                "competitors": ["Unknown"],
                "recent_news": ["No live data available"],
                "linkedin_data": "Unavailable",
                "founded": None,
                "employee_count": None,
                "headquarters": None,
                "raw_web_content": "",
            })

        return "Fallback response generated because the configured LLM provider was unavailable."

    async def generate(self, prompt: str, temperature: float = 0.3) -> str:
        """Generate text from a prompt. Returns the text response."""
        try:
            client = self._get_client()
        except Exception as exc:
            logger.warning("LLM client unavailable, using fallback generation: %s", exc)
            return self._fallback_response(prompt)

        if self._provider == "gemini":
            import asyncio
            import functools

            loop = asyncio.get_event_loop()
            candidate_models = [self._settings.gemini_model, "gemini-2.5-flash", "gemini-2.5-flash-lite",]
            candidate_models = list(dict.fromkeys([m for m in candidate_models if m]))

            last_exc = None
            for model_name in candidate_models:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=self._settings.gemini_api_key)
                    model = genai.GenerativeModel(model_name)
                    response = await loop.run_in_executor(
                        None,
                        functools.partial(
                            model.generate_content,
                            prompt,
                            generation_config={"temperature": temperature},
                        ),
                    )
                    return response.text
                except Exception as exc:
                    last_exc = exc
                    if "404" in str(exc) or "not found" in str(exc):
                        logger.warning("Gemini model '%s' failed (404). Trying next fallback model...", model_name)
                        continue
                    logger.warning("Gemini request failed for '%s': %s", model_name, exc)
                    break
            if last_exc is not None:
                logger.warning("Falling back to deterministic content because Gemini generation failed: %s", last_exc)
            return self._fallback_response(prompt)

        elif self._provider == "openai":
            try:
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                )
                return response.choices[0].message.content or ""
            except Exception as exc:
                logger.warning("OpenAI request failed, using fallback generation: %s", exc)
                return self._fallback_response(prompt)

        elif self._provider == "claude":
            try:
                response = await client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=8096,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                )
                return response.content[0].text
            except Exception as exc:
                logger.warning("Anthropic request failed, using fallback generation: %s", exc)
                return self._fallback_response(prompt)

        raise ValueError(f"Unsupported provider: {self._provider}")


# Module-level singleton factory
_llm_instance: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMClient()
    return _llm_instance
