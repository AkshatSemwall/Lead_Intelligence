"""
Central configuration for Lead Intelligence.
All values are sourced from environment variables / .env file.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────────────────────────────
    gemini_api_key: str = ""
    llm_provider: Literal["gemini", "claude", "openai"] = "gemini"
    gemini_model: str = "gemini-1.5-flash"
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # ── Research ─────────────────────────────────────────────────────────
    tavily_api_key: str = ""
    firecrawl_api_key: str = ""

    # ── Google OAuth ──────────────────────────────────────────────────────
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""

    # ── Google APIs ───────────────────────────────────────────────────────
    google_sheet_id: str = ""
    google_drive_folder_id: str = ""
    gmail_sender_email: str = ""

    # ── App ───────────────────────────────────────────────────────────────
    app_name: str = "Lead Intelligence"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    api_key: str = ""
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    # ── LangGraph / Workflow ───────────────────────────────────────────────
    max_retries: int = 3
    retry_delay_seconds: float = 2.0

    @field_validator("gemini_api_key", "openai_api_key", "anthropic_api_key", mode="before")
    @classmethod
    def _strip_secret(cls, value: str | None) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("llm_provider")
    @classmethod
    def _validate_provider(cls, value: str) -> str:
        provider = value.lower()
        if provider not in {"gemini", "claude", "openai"}:
            raise ValueError("llm_provider must be one of: gemini, claude, openai")
        return provider

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_required_settings(self) -> "Settings":
        provider = self.llm_provider
        if provider == "gemini" and not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        if provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        if provider == "claude" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=claude")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
