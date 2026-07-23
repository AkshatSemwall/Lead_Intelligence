"""
Firecrawl client for deep website crawling and scraping.
"""
from __future__ import annotations

import logging
from typing import Any

from backend.utils.helpers import retry_async

logger = logging.getLogger(__name__)


class FirecrawlClient:
    def __init__(self, settings: Any | None = None) -> None:
        from backend.config import get_settings

        self._settings = settings or get_settings()
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            api_key = getattr(self._settings, "firecrawl_api_key", None)
            if not api_key:
                self._client = None
                return None
            from firecrawl import FirecrawlApp  # type: ignore

            self._client = FirecrawlApp(api_key=api_key)
        return self._client

    async def scrape_website(self, url: str) -> str:
        """
        Scrape a website URL and return clean markdown text content.
        Falls back gracefully if Firecrawl is unavailable.
        """
        import asyncio
        import functools

        client = self._get_client()
        if client is None:
            return ""
        loop = asyncio.get_event_loop()

        async def _do_scrape() -> str:
            result = await loop.run_in_executor(
                None,
                functools.partial(
                    client.scrape,
                    url,
                    formats=["markdown"],
                    only_main_content=True,
                ),
            )
            markdown = ""
            if isinstance(result, dict):
                markdown = result.get("markdown", "") or result.get("content", "")
            elif hasattr(result, "markdown"):
                markdown = result.markdown or ""
            elif hasattr(result, "content"):
                markdown = result.content or ""
            return markdown[:15_000]

        try:
            return await retry_async(_do_scrape, max_retries=2, delay=1.0)
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
        if client is None:
            return []
        loop = asyncio.get_event_loop()

        async def _do_crawl() -> list[dict[str, str]]:
            result = await loop.run_in_executor(
                None,
                functools.partial(
                    client.crawl,
                    url,
                    limit=page_limit,
                    scrape_options={"formats": ["markdown"], "only_main_content": True},
                ),
            )
            pages: list[dict[str, str]] = []
            data: list[Any] = []
            if isinstance(result, list):
                data = result
            elif isinstance(result, dict):
                data = result.get("data", []) or result.get("pages", []) or []
            elif hasattr(result, "data"):
                data = getattr(result, "data", []) or []
            elif hasattr(result, "pages"):
                data = getattr(result, "pages", []) or []
            for page in data:
                if isinstance(page, dict):
                    markdown = page.get("markdown", "") or page.get("content", "") or ""
                    metadata = page.get("metadata", {}) or {}
                    page_url = metadata.get("sourceURL") or page.get("url") or url
                    pages.append({"url": page_url, "markdown": markdown[:5000]})
                elif hasattr(page, "markdown"):
                    page_url = getattr(getattr(page, "metadata", None), "sourceURL", None) or getattr(page, "url", None) or url
                    markdown = getattr(page, "markdown", "") or getattr(page, "content", "") or ""
                    pages.append({"url": page_url, "markdown": markdown[:5000]})
            return pages

        try:
            return await retry_async(_do_crawl, max_retries=2, delay=1.0)
        except Exception as exc:
            logger.warning("Firecrawl crawl failed for '%s': %s", url, exc)
            return []


_firecrawl_instance: FirecrawlClient | None = None


def get_firecrawl_client() -> FirecrawlClient:
    global _firecrawl_instance
    if _firecrawl_instance is None:
        _firecrawl_instance = FirecrawlClient()
    return _firecrawl_instance
