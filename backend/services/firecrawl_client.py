"""
Firecrawl client for deep website crawling and scraping.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class FirecrawlClient:
    def __init__(self, settings: Any | None = None) -> None:
        from backend.config import get_settings

        self._settings = settings or get_settings()
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from firecrawl import FirecrawlApp  # type: ignore

            self._client = FirecrawlApp(api_key=self._settings.firecrawl_api_key)
        return self._client

    async def scrape_website(self, url: str) -> str:
        """
        Scrape a website URL and return clean markdown text content.
        Falls back gracefully if Firecrawl is unavailable.
        """
        import asyncio
        import functools

        client = self._get_client()
        loop = asyncio.get_event_loop()

        try:
            result = await loop.run_in_executor(
                None,
                functools.partial(
                    client.scrape_url,
                    url,
                    params={"formats": ["markdown"], "onlyMainContent": True},
                ),
            )
            markdown = ""
            if isinstance(result, dict):
                markdown = result.get("markdown", "") or result.get("content", "")
            elif hasattr(result, "markdown"):
                markdown = result.markdown or ""
            return markdown[:15_000]  # cap to avoid token overflow
        except Exception as exc:
            logger.warning("Firecrawl scrape failed for '%s': %s", url, exc)
            return ""

    async def crawl_website(self, url: str, page_limit: int = 5) -> list[dict[str, str]]:
        """
        Crawl multiple pages of a website.
        Returns list of {url, markdown} dicts.
        """
        import asyncio
        import functools

        client = self._get_client()
        loop = asyncio.get_event_loop()

        try:
            result = await loop.run_in_executor(
                None,
                functools.partial(
                    client.crawl_url,
                    url,
                    params={
                        "limit": page_limit,
                        "scrapeOptions": {"formats": ["markdown"]},
                    },
                ),
            )
            pages = []
            data = result if isinstance(result, list) else result.get("data", []) if isinstance(result, dict) else []
            for page in data:
                if isinstance(page, dict):
                    pages.append(
                        {
                            "url": page.get("metadata", {}).get("sourceURL", url),
                            "markdown": page.get("markdown", "")[:5000],
                        }
                    )
            return pages
        except Exception as exc:
            logger.warning("Firecrawl crawl failed for '%s': %s", url, exc)
            return []


_firecrawl_instance: FirecrawlClient | None = None


def get_firecrawl_client() -> FirecrawlClient:
    global _firecrawl_instance
    if _firecrawl_instance is None:
        _firecrawl_instance = FirecrawlClient()
    return _firecrawl_instance
