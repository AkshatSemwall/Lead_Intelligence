"""
Logging Agent — records workflow execution summary and persists structured logs.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.models.state import WorkflowState
from backend.utils.helpers import make_log_entry, now_iso, compute_progress

logger = logging.getLogger(__name__)

LOG_DIR = Path("workflow_logs")
LOG_DIR.mkdir(exist_ok=True)


async def logging_node(state: WorkflowState) -> WorkflowState:
    """LangGraph node: Persist structured execution logs."""
    log_entries = list(state.get("log_entries", []))
    workflow_id = state.get("workflow_id", "unknown")

    summary = {
        "workflow_id": workflow_id,
        "lead_email": state.get("lead_email", ""),
        "lead_company": state.get("lead_company", ""),
        "status": state.get("status", "unknown"),
        "nodes_completed": state.get("nodes_completed", []),
        "email_sent": state.get("email_sent", False),
        "pdf_generated": bool(state.get("pdf_path")),
        "drive_url": state.get("drive_url"),
        "errors": {
            "validation": state.get("validation_error"),
            "research": state.get("research_error"),
            "analysis": state.get("analysis_error"),
            "insights": state.get("insights_error"),
            "report": state.get("report_error"),
            "pdf": state.get("pdf_error"),
            "email": state.get("email_error"),
            "sheets": state.get("sheets_error"),
            "drive": state.get("drive_error"),
        },
        "log_entries": log_entries,
        "completed_at": now_iso(),
    }

    # Write JSON log file
    log_path = LOG_DIR / f"{workflow_id}.json"
    try:
        log_path.write_text(json.dumps(summary, indent=2, default=str))
        logger.info("Workflow log written to %s", log_path)
    except Exception as exc:
        logger.error("Failed to write log file: %s", exc)

    log_entries.append(make_log_entry("logging", "completed", f"Logs saved to {log_path}"))
    nodes_completed = list(state.get("nodes_completed", []))
    nodes_completed.append("logging")
    progress = compute_progress(nodes_completed)

    return {
        **state,
        "log_entries": log_entries,
        "nodes_completed": nodes_completed,
        "current_node": "logging",
        "progress_pct": progress,
    }
