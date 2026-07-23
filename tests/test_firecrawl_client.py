import asyncio

from backend.services.firecrawl_client import FirecrawlClient


def test_firecrawl_client_handles_missing_api_key_gracefully() -> None:
    client = FirecrawlClient(settings=type("Settings", (), {"firecrawl_api_key": None})())

    async def run() -> None:
        markdown = await client.scrape_website("https://example.com")
        pages = await client.crawl_website("https://example.com", page_limit=2)

        assert markdown == ""
        assert pages == []

    asyncio.run(run())
