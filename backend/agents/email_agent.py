"""
Email Agent — sends personalised email with PDF attachment via Gmail API.
"""
from __future__ import annotations

import logging

from backend.models.state import WorkflowState
from backend.services.gmail_service import get_gmail_service
from backend.utils.helpers import make_log_entry

logger = logging.getLogger(__name__)


async def email_node(state: WorkflowState) -> WorkflowState:
    """LangGraph node: Send report email with PDF attachment."""
    log_entries = list(state.get("log_entries", []))
    log_entries.append(make_log_entry("email", "started", "Sending report email"))

    lead_email = state.get("lead_email", "")
    lead_name = state.get("lead_name", "")
    company = state.get("lead_company", "")
    pdf_path = state.get("pdf_path")
    drive_url = state.get("drive_url")

    if not lead_email:
        error = "No email address available"
        log_entries.append(make_log_entry("email", "failed", error, error=error))
        return {
            **state,
            "email_sent": False,
            "email_error": error,
            "log_entries": log_entries,
            "current_node": "email",
        }

    try:
        gmail = get_gmail_service()
        success = await gmail.send_report_email(
            to_email=lead_email,
            lead_name=lead_name,
            company_name=company,
            pdf_path=pdf_path,
            drive_url=drive_url,
        )

        if success:
            log_entries.append(make_log_entry("email", "completed", f"Email sent to {lead_email}"))
        else:
            log_entries.append(make_log_entry("email", "failed", "Gmail API returned failure", error="Send failed"))

        nodes_completed = list(state.get("nodes_completed", []))
        if success:
            nodes_completed.append("email")

        return {
            **state,
            "email_sent": success,
            "email_error": None if success else "Gmail API send failed",
            "log_entries": log_entries,
            "nodes_completed": nodes_completed,
            "current_node": "email",
        }

    except Exception as exc:
        logger.error("Email agent failed: %s", exc, exc_info=True)
        log_entries.append(make_log_entry("email", "failed", str(exc), error=str(exc)))

        return {
            **state,
            "email_sent": False,
            "email_error": str(exc),
            "log_entries": log_entries,
            "current_node": "email",
        }
