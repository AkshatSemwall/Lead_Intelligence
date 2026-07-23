"""
Report Generation Agent — generates the full Markdown consulting report.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from backend.models.state import WorkflowState
from backend.prompts.templates import report_generation_prompt
from backend.services.gemini_client import get_llm_client
from backend.utils.helpers import make_log_entry

logger = logging.getLogger(__name__)


def build_structured_report(
    lead_name: str,
    company: str,
    website: str,
    research: dict[str, Any] | None = None,
    analysis: dict[str, Any] | None = None,
    insights: dict[str, Any] | None = None,
) -> str:
    """Build a structured business-audit report that follows the project workflow."""
    research = research or {}
    analysis = analysis or {}
    insights = insights or {}

    website_audit = insights.get("website_audit", {})
    recommendations = insights.get("recommendations", [])
    automation_opportunities = insights.get("automation_opportunities", [])
    priority_actions = insights.get("priority_actions", [])
    pain_points = analysis.get("pain_points", [])
    strengths = analysis.get("strengths", [])
    business_model = analysis.get("business_model", "Business model information unavailable")
    industry = research.get("industry", "Industry information unavailable")
    description = research.get("description", "Company profile is currently limited to the available workflow input.")

    return f"""# Executive Summary

For {lead_name}, this business audit highlights the most important opportunities for {company} to improve growth, efficiency, and digital maturity. Based on the available company research and workflow findings, the company appears to operate in the {industry} space and is positioned to benefit from more structured digital operations, clearer customer journeys, and targeted automation. The report below captures the core business context, current website and experience insights, high-value AI opportunities, and a practical 90-day roadmap.

The analysis emphasises how {company} can turn its current strengths into a more scalable operating model. Key themes include tightening customer acquisition processes, modernising the online experience, and using AI to automate repetitive workflows. Together, these actions can improve conversion rates, reduce manual effort, and create a stronger foundation for long-term growth.

# Company Overview

## Business Context
- Company: {company}
- Website: {website}
- Industry: {industry}
- Business model: {business_model}

## Company Profile
{description}

## What the business should prioritise
- Strengthen the core value proposition across the website and sales journey.
- Harness available data more effectively to support better decisions.
- Introduce automation in areas such as lead handling, reporting, and follow-up.

# Website Analysis

## Design & User Experience
The current website experience should be reviewed with a focus on clarity, trust signals, and call-to-action strength. The available audit signals suggest a moderate-to-strong foundation, with room to improve the path from first visit to conversion. Optimising messaging, social proof, and navigation structure can materially improve engagement.

## Content Strategy
The content strategy should align more closely with the target customer journey. Messaging should be concise, specific, and tailored to buyer needs. Highlighting outcomes, proof points, and next steps will strengthen the persuasive impact of the site.

## Technical Performance
The site should be reviewed for page speed, structure, and the overall quality of the conversion experience. Faster, simpler pages improve bounce rates and give the business a better online impression.

## SEO Assessment
Search visibility should be improved through stronger on-page optimisation, clearer page hierarchy, and content that reflects the products, services, and customer pain points identified during the workflow.

# AI & Automation Opportunities

## Quick Wins (0-3 months)
- Automate lead capture and triage workflows.
- Use AI to generate follow-up emails and meeting summaries.
- Create structured reports and internal summaries from existing data sources.

## Medium-term Initiatives (3-12 months)
- Deploy a conversational assistant for prospect qualification.
- Introduce AI-powered content personalisation.
- Automate repetitive back-office and reporting workflows.

## Strategic AI Roadmap (12+ months)
- Build AI-enabled decision support for sales and operations.
- Embed predictive monitoring into customer lifecycle workflows.
- Create a connected automation stack that scales with business complexity.

# Strategic Recommendations

- Improve the website conversion path to make it easier for visitors to take the next step.
- Focus on the highest-value pain points first, especially those that create operational drag.
- Use automation to reduce repetitive tasks and free up teams for higher-value work.
- Strengthen the quality and consistency of customer-facing communications.
- Prioritise the most impactful AI use cases around growth, efficiency, and service delivery.

# Next Steps

## Immediate Actions (Week 1-2)
- Validate the core business message and messaging hierarchy.
- Review the current website journey for friction points.
- Create a shortlist of high-priority automation opportunities.

## Month 1 Priorities
- Prepare a 30-60-90 day implementation plan.
- Align stakeholders around the recommended initiatives.
- Begin quick-win automation pilots.

## 90-Day Milestones
- Launch the first automation workflow.
- Improve conversion-focused content and website experience.
- Establish ongoing reporting and review cadence for the next phase of growth.

---
*Report generated by Lead Intelligence AI as part of the autonomous multi-agent workflow.*
"""


async def report_generation_node(state: WorkflowState) -> WorkflowState:
    """LangGraph node: Generate comprehensive Markdown business audit report."""
    log_entries = list(state.get("log_entries", []))
    log_entries.append(make_log_entry("report_generation", "started", "Generating report"))

    lead_name = state.get("lead_name", "")
    company = state.get("lead_company", "")
    website = state.get("lead_website", "")
    research = state.get("research") or {}
    analysis = state.get("analysis") or {}
    insights = state.get("insights") or {}

    try:
        llm = get_llm_client()

        research_text = json.dumps(
            {k: v for k, v in research.items() if k != "raw_web_content"},
            indent=2,
        )
        analysis_text = json.dumps(analysis, indent=2)
        insights_text = json.dumps(insights, indent=2)

        prompt = report_generation_prompt(
            lead_name=lead_name,
            company_name=company,
            website=website,
            research_data=research_text,
            analysis_data=analysis_text,
            insight_data=insights_text,
        )

        # Use higher temperature for more natural prose
        report_markdown = await llm.generate(prompt, temperature=0.4)

        log_entries.append(make_log_entry("report_generation", "completed", "Report generated"))
        nodes_completed = list(state.get("nodes_completed", []))
        nodes_completed.append("report_generation")

        return {
            **state,
            "report_markdown": report_markdown,
            "report_error": None,
            "log_entries": log_entries,
            "nodes_completed": nodes_completed,
            "current_node": "report_generation",
        }

    except Exception as exc:
        logger.error("Report generation failed: %s", exc, exc_info=True)
        log_entries.append(make_log_entry("report_generation", "failed", str(exc), error=str(exc)))

        fallback_report = build_structured_report(
            lead_name=lead_name,
            company=company,
            website=website,
            research=research,
            analysis=analysis,
            insights=insights,
        )

        return {
            **state,
            "report_markdown": fallback_report,
            "report_error": str(exc),
            "log_entries": log_entries,
            "current_node": "report_generation",
        }
