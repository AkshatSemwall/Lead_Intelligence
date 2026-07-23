"""
PDF Generation Agent — converts Markdown report to a professional PDF via WeasyPrint.
"""
from __future__ import annotations

import logging

from backend.models.state import WorkflowState
from backend.services.pdf_service import generate_pdf
from backend.utils.helpers import make_log_entry

logger = logging.getLogger(__name__)


async def pdf_generation_node(state: WorkflowState) -> WorkflowState:
    """LangGraph node: Convert Markdown report to PDF."""
    log_entries = list(state.get("log_entries", []))
    log_entries.append(make_log_entry("pdf_generation", "started", "Generating PDF"))

    report_markdown = state.get("report_markdown", "")
    company = state.get("lead_company", "Unknown Company")
    lead_name = state.get("lead_name", "")
    workflow_id = state.get("workflow_id", "unknown")

    if not report_markdown:
        error = "No report markdown available for PDF generation"
        log_entries.append(make_log_entry("pdf_generation", "failed", error, error=error))
        return {
            **state,
            "pdf_path": None,
            "pdf_error": error,
            "log_entries": log_entries,
            "current_node": "pdf_generation",
        }

    try:
        pdf_path = await generate_pdf(
            markdown_content=report_markdown,
            company_name=company,
            lead_name=lead_name,
            workflow_id=workflow_id,
        )

        log_entries.append(make_log_entry("pdf_generation", "completed", f"PDF saved at {pdf_path}"))
        nodes_completed = list(state.get("nodes_completed", []))
        nodes_completed.append("pdf_generation")

        return {
            **state,
            "pdf_path": pdf_path,
            "pdf_error": None,
            "log_entries": log_entries,
            "nodes_completed": nodes_completed,
            "current_node": "pdf_generation",
        }

    except Exception as exc:
        logger.error("PDF generation failed: %s", exc, exc_info=True)
        log_entries.append(make_log_entry("pdf_generation", "failed", str(exc), error=str(exc)))

        return {
            **state,
            "pdf_path": None,
            "pdf_error": str(exc),
            "log_entries": log_entries,
            "current_node": "pdf_generation",
        }
