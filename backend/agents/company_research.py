"""
Company Research Agent — crawls website and searches web for company intelligence.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from backend.models.state import WorkflowState, CompanyResearchData
from backend.prompts.templates import company_research_prompt
from backend.services.gemini_client import get_llm_client
from backend.services.tavily_client import get_tavily_client
from backend.services.firecrawl_client import get_firecrawl_client
from backend.utils.helpers import extract_json, make_log_entry, now_iso

logger = logging.getLogger(__name__)


async def company_research_node(state: WorkflowState) -> WorkflowState:
    """LangGraph node: Research company from web and website crawl."""
    log_entries = list(state.get("log_entries", []))
    log_entries.append(make_log_entry("company_research", "started", "Starting company research"))

    company = state.get("lead_company", "")
    website = state.get("lead_website", "")

    try:
        # 1. Crawl website with Firecrawl
        firecrawl = get_firecrawl_client()
        website_content = await firecrawl.scrape_website(website)
        crawled_pages = await firecrawl.crawl_website(website, page_limit=3)

        # Combine crawled content
        all_web_content = website_content
        for page in crawled_pages:
            all_web_content += f"\n\n--- {page['url']} ---\n{page['markdown']}"

        # 2. Search web with Tavily
        tavily = get_tavily_client()
        search_results = await tavily.search_company(company, website)

        search_text = "\n\n".join(
            f"Source: {r['url']}\nTitle: {r['title']}\n{r['content']}"
            for r in search_results
        )

        # 3. LLM extraction
        llm = get_llm_client()
        prompt = company_research_prompt(company, website, all_web_content, search_text)
        raw = await llm.generate(prompt, temperature=0.1)

        data_dict = extract_json(raw)
        if not data_dict:
            raise ValueError(f"LLM returned unparseable response: {raw[:200]}")

        # Store raw web content for downstream agents
        data_dict["raw_web_content"] = all_web_content[:8000]
        data_dict.setdefault("company_name", company)
        data_dict.setdefault("website_url", website)

        research_data = CompanyResearchData(**{k: v for k, v in data_dict.items() if k in CompanyResearchData.model_fields})

        log_entries.append(make_log_entry("company_research", "completed", f"Researched {company} successfully"))
        nodes_completed = list(state.get("nodes_completed", []))
        nodes_completed.append("company_research")

        return {
            **state,
            "research": research_data.model_dump(),
            "research_error": None,
            "log_entries": log_entries,
            "nodes_completed": nodes_completed,
            "current_node": "company_research",
        }

    except Exception as exc:
        logger.error("Company research failed: %s", exc, exc_info=True)
        log_entries.append(make_log_entry("company_research", "failed", str(exc), error=str(exc)))

        # Fallback minimal research data so pipeline can continue
        fallback = CompanyResearchData(
            company_name=company,
            website_url=website,
            description=f"Research data unavailable for {company}. Error: {exc}",
        )

        return {
            **state,
            "research": fallback.model_dump(),
            "research_error": str(exc),
            "log_entries": log_entries,
            "current_node": "company_research",
        }
