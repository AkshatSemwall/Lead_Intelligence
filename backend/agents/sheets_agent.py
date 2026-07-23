"""
Google Sheets Agent — logs lead and workflow data to Google Sheets.
"""
from __future__ import annotations

import logging

from backend.models.state import WorkflowState
from backend.services.sheets_service import get_sheets_service
from backend.utils.helpers import make_log_entry

logger = logging.getLogger(__name__)


async def sheets_node(state: WorkflowState) -> WorkflowState:
    """LangGraph node: Store lead data and workflow status in Google Sheets."""
    log_entries = list(state.get("log_entries", []))
    log_entries.append(make_log_entry("sheets", "started", "Writing to Google Sheets"))

    try:
        sheets = get_sheets_service()
        await sheets.ensure_header_row()

        row_range = await sheets.append_lead_row(
            workflow_id=state.get("workflow_id", ""),
            lead_name=state.get("lead_name", ""),
            lead_email=state.get("lead_email", ""),
            company=state.get("lead_company", ""),
            website=state.get("lead_website", ""),
            status=state.get("status", "completed"),
            email_sent=state.get("email_sent", False),
            drive_url=state.get("drive_url"),
            report_generated=bool(state.get("report_markdown")),
            error=state.get("error"),
        )

        log_entries.append(make_log_entry("sheets", "completed", f"Row appended: {row_range}"))
        nodes_completed = list(state.get("nodes_completed", []))
        nodes_completed.append("sheets")

        return {
            **state,
            "sheet_row_id": row_range,
            "sheets_error": None,
            "log_entries": log_entries,
            "nodes_completed": nodes_completed,
            "current_node": "sheets",
        }

    except Exception as exc:
        logger.error("Sheets agent failed: %s", exc, exc_info=True)
        log_entries.append(make_log_entry("sheets", "failed", str(exc), error=str(exc)))

        return {
            **state,
            "sheet_row_id": None,
            "sheets_error": str(exc),
            "log_entries": log_entries,
            "current_node": "sheets",
        }
