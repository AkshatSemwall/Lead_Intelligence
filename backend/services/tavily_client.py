"""
Tavily search client for web research.
"""
from __future__ import annotations

import logging
from typing import Any

from backend.utils.helpers import retry_async

logger = logging.getLogger(__name__)


class TavilyClient:
    def __init__(self, settings: Any | None = None) -> None:
        from backend.config import get_settings

        self._settings = settings or get_settings()
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from tavily import TavilyClient as _Tavily  # type: ignore

            self._client = _Tavily(api_key=self._settings.tavily_api_key)
        return self._client

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
    ) -> list[dict[str, str]]:
        """
        Perform a web search via Tavily.
        Returns list of {title, url, content} dicts.
        """
        import asyncio
        import functools

        client = self._get_client()
        loop = asyncio.get_event_loop()

        async def _do_search() -> list[dict[str, str]]:
            result = await loop.run_in_executor(
                None,
                functools.partial(
                    client.search,
                    query=query,
                    max_results=max_results,
                    search_depth=search_depth,
                    include_raw_content=True,
                ),
            )
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                    "raw_content": r.get("raw_content", "") or "",
                }
                for r in result.get("results", [])
            ]

        try:
            return await retry_async(_do_search, max_retries=2, delay=1.0)
        except Exception as exc:
            logger.warning("Tavily search failed for query '%s': %s", query, exc)
            return []

    async def search_company(self, company: str, website: str) -> list[dict[str, str]]:
        queries = [
            f"{company} company overview services products",
            f"{company} {website} business model",
            f"{company} news 2024 2025",
            f"{company} competitors industry",
            f"site:linkedin.com/company {company}",
        ]
        results: list[dict[str, str]] = []
        for q in queries:
            results.extend(await self.search(q, max_results=3))
        return results


_tavily_instance: TavilyClient | None = None


def get_tavily_client() -> TavilyClient:
    global _tavily_instance
    if _tavily_instance is None:
        _tavily_instance = TavilyClient()
    return _tavily_instance
