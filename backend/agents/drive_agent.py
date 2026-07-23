"""
Google Drive Agent — uploads generated PDF to Google Drive and returns a shareable URL.
"""
from __future__ import annotations

import logging

from backend.models.state import WorkflowState
from backend.services.drive_service import get_drive_service
from backend.utils.helpers import make_log_entry

logger = logging.getLogger(__name__)


async def drive_node(state: WorkflowState) -> WorkflowState:
    """LangGraph node: Upload PDF to Google Drive."""
    log_entries = list(state.get("log_entries", []))
    log_entries.append(make_log_entry("drive", "started", "Uploading PDF to Google Drive"))

    pdf_path = state.get("pdf_path")
    company = state.get("lead_company", "Unknown")
    workflow_id = state.get("workflow_id", "unknown")

    if not pdf_path:
        error = "No PDF available for Drive upload"
        log_entries.append(make_log_entry("drive", "skipped", error))
        return {
            **state,
            "drive_url": None,
            "drive_file_id": None,
            "drive_error": error,
            "log_entries": log_entries,
            "current_node": "drive",
        }

    try:
        drive = get_drive_service()
        file_id, drive_url = await drive.upload_pdf(
            pdf_path=pdf_path,
            company_name=company,
            workflow_id=workflow_id,
        )

        if drive_url:
            log_entries.append(make_log_entry("drive", "completed", f"PDF uploaded: {drive_url}"))
            nodes_completed = list(state.get("nodes_completed", []))
            nodes_completed.append("drive")
        else:
            log_entries.append(make_log_entry("drive", "failed", "Upload returned no URL", error="No URL returned"))
            nodes_completed = list(state.get("nodes_completed", []))

        return {
            **state,
            "drive_url": drive_url,
            "drive_file_id": file_id,
            "drive_error": None if drive_url else "Upload failed",
            "log_entries": log_entries,
            "nodes_completed": nodes_completed,
            "current_node": "drive",
        }

    except Exception as exc:
        logger.error("Drive agent failed: %s", exc, exc_info=True)
        log_entries.append(make_log_entry("drive", "failed", str(exc), error=str(exc)))

        return {
            **state,
            "drive_url": None,
            "drive_file_id": None,
            "drive_error": str(exc),
            "log_entries": log_entries,
            "current_node": "drive",
        }
