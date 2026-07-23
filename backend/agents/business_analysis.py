"""
Business Analysis Agent — analyzes business model, strengths, weaknesses, AI opportunities.
"""
from __future__ import annotations

import json
import logging

from backend.models.state import WorkflowState, BusinessAnalysisData
from backend.prompts.templates import business_analysis_prompt
from backend.services.gemini_client import get_llm_client
from backend.utils.helpers import extract_json, make_log_entry

logger = logging.getLogger(__name__)


async def business_analysis_node(state: WorkflowState) -> WorkflowState:
    """LangGraph node: Analyze the company's business."""
    log_entries = list(state.get("log_entries", []))
    log_entries.append(make_log_entry("business_analysis", "started", "Starting business analysis"))

    company = state.get("lead_company", "")
    research = state.get("research") or {}
    web_content = research.get("raw_web_content", "")

    try:
        llm = get_llm_client()
        research_text = json.dumps(
            {k: v for k, v in research.items() if k != "raw_web_content"},
            indent=2,
        )
        prompt = business_analysis_prompt(company, research_text, web_content)
        raw = await llm.generate(prompt, temperature=0.2)

        data_dict = extract_json(raw)
        if not data_dict:
            raise ValueError(f"LLM returned unparseable JSON: {raw[:300]}")

        analysis = BusinessAnalysisData(**{k: v for k, v in data_dict.items() if k in BusinessAnalysisData.model_fields})

        log_entries.append(make_log_entry("business_analysis", "completed", "Business analysis complete"))
        nodes_completed = list(state.get("nodes_completed", []))
        nodes_completed.append("business_analysis")

        return {
            **state,
            "analysis": analysis.model_dump(),
            "analysis_error": None,
            "log_entries": log_entries,
            "nodes_completed": nodes_completed,
            "current_node": "business_analysis",
        }

    except Exception as exc:
        logger.error("Business analysis failed: %s", exc, exc_info=True)
        log_entries.append(make_log_entry("business_analysis", "failed", str(exc), error=str(exc)))

        fallback = BusinessAnalysisData(
            business_model="Analysis unavailable",
            target_audience="Unknown",
            pain_points=["Analysis failed — using fallback data"],
            ai_opportunities=["Automated data analysis", "Customer support automation"],
        )

        return {
            **state,
            "analysis": fallback.model_dump(),
            "analysis_error": str(exc),
            "log_entries": log_entries,
            "current_node": "business_analysis",
        }
