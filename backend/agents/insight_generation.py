"""
Insight Generation Agent — generates website audit, recommendations, and automation opportunities.
"""
from __future__ import annotations

import json
import logging

from backend.models.state import WorkflowState, InsightData
from backend.prompts.templates import insight_generation_prompt
from backend.services.gemini_client import get_llm_client
from backend.utils.helpers import extract_json, make_log_entry

logger = logging.getLogger(__name__)


async def insight_generation_node(state: WorkflowState) -> WorkflowState:
    """LangGraph node: Generate actionable insights and website audit."""
    log_entries = list(state.get("log_entries", []))
    log_entries.append(make_log_entry("insight_generation", "started", "Generating insights"))

    company = state.get("lead_company", "")
    website = state.get("lead_website", "")
    research = state.get("research") or {}
    analysis = state.get("analysis") or {}
    web_content = research.get("raw_web_content", "")

    try:
        llm = get_llm_client()
        analysis_text = json.dumps(analysis, indent=2)
        prompt = insight_generation_prompt(company, website, web_content, analysis_text)
        raw = await llm.generate(prompt, temperature=0.3)

        data_dict = extract_json(raw)
        if not data_dict:
            raise ValueError(f"LLM returned unparseable JSON: {raw[:300]}")

        insights = InsightData(**{k: v for k, v in data_dict.items() if k in InsightData.model_fields})

        log_entries.append(make_log_entry("insight_generation", "completed", "Insights generated"))
        nodes_completed = list(state.get("nodes_completed", []))
        nodes_completed.append("insight_generation")

        return {
            **state,
            "insights": insights.model_dump(),
            "insights_error": None,
            "log_entries": log_entries,
            "nodes_completed": nodes_completed,
            "current_node": "insight_generation",
        }

    except Exception as exc:
        logger.error("Insight generation failed: %s", exc, exc_info=True)
        log_entries.append(make_log_entry("insight_generation", "failed", str(exc), error=str(exc)))

        fallback = InsightData(
            website_audit={"design_score": 5, "ux_score": 5, "content_score": 5, "seo_score": 5},
            recommendations=["Improve digital presence", "Implement AI chatbot"],
            automation_opportunities=["Email automation", "Data entry automation"],
            business_improvements=["Process optimisation"],
            priority_actions=["Conduct full audit"],
            estimated_impact="Moderate positive impact expected",
        )

        return {
            **state,
            "insights": fallback.model_dump(),
            "insights_error": str(exc),
            "log_entries": log_entries,
            "current_node": "insight_generation",
        }
