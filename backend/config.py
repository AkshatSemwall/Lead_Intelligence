"""
Central configuration for Lead Intelligence.
All values are sourced from environment variables / .env file.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

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

    # ── LangGraph / Workflow ───────────────────────────────────────────────
    max_retries: int = 3
    retry_delay_seconds: float = 2.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
