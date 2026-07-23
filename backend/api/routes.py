"""
FastAPI route handlers for the Lead Intelligence API.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from backend.api.store import save_state, get_state, list_workflow_ids
from backend.graph.workflow import get_workflow
from backend.models.state import WorkflowState
from backend.models import (
    LeadSubmissionRequest,
    LeadSubmissionResponse,
    WorkflowStatusResponse,
    ReportResponse,
    HealthResponse,
)
from backend.utils.helpers import now_iso, compute_progress

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Background task runner ───────────────────────────────────────────────────


async def _run_workflow(workflow_id: str, initial_state: WorkflowState) -> None:
    """Execute the LangGraph workflow in the background."""
    try:
        workflow = get_workflow()
        final_state: WorkflowState = await workflow.ainvoke(initial_state)  # type: ignore
        final_state["workflow_id"] = workflow_id
        await save_state(workflow_id, final_state)
        logger.info("Workflow %s completed with status: %s", workflow_id, final_state.get("status"))
    except Exception as exc:
        logger.error("Workflow %s failed with unhandled exception: %s", workflow_id, exc, exc_info=True)
        error_state: WorkflowState = {
            **initial_state,
            "status": "failed",
            "error": str(exc),
            "completed_at": now_iso(),
            "current_node": "error",
        }
        await save_state(workflow_id, error_state)


# ─── Routes ───────────────────────────────────────────────────────────────────


@router.post("/submit-lead", response_model=LeadSubmissionResponse, status_code=202)
async def submit_lead(
    payload: LeadSubmissionRequest,
    background_tasks: BackgroundTasks,
) -> LeadSubmissionResponse:
    """Accept a lead form submission and trigger the autonomous workflow."""
    workflow_id = str(uuid.uuid4())
    submitted_at = datetime.utcnow()

    initial_state: WorkflowState = {
        "workflow_id": workflow_id,
        "submitted_at": submitted_at.isoformat() + "Z",
        "lead_name": payload.name,
        "lead_email": str(payload.email),
        "lead_company": payload.company,
        "lead_website": payload.website,
        "lead_phone": payload.phone or "",
        "lead_message": payload.message or "",
        "status": "pending",
        "current_node": None,
        "nodes_completed": [],
        "log_entries": [],
        "retry_counts": {},
        "email_sent": False,
        "progress_pct": 0,
    }

    await save_state(workflow_id, initial_state)

    background_tasks.add_task(_run_workflow, workflow_id, initial_state)

    logger.info("Lead submitted — workflow_id=%s email=%s", workflow_id, payload.email)

    return LeadSubmissionResponse(
        workflow_id=workflow_id,
        status="pending",
        message="Your information has been received. We are generating your personalised audit report.",
        submitted_at=submitted_at,
    )


@router.get("/workflow-status/{workflow_id}", response_model=WorkflowStatusResponse)
async def workflow_status(workflow_id: str) -> WorkflowStatusResponse:
    """Retrieve the current status of a workflow execution."""
    state = await get_state(workflow_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

    nodes_completed = state.get("nodes_completed", [])

    return WorkflowStatusResponse(
        workflow_id=workflow_id,
        status=state.get("status", "unknown"),
        current_node=state.get("current_node"),
        progress_pct=state.get("progress_pct", compute_progress(nodes_completed)),
        started_at=_parse_dt(state.get("started_at")),
        completed_at=_parse_dt(state.get("completed_at")),
        error=state.get("error"),
        nodes_completed=nodes_completed,
    )


@router.get("/report/{workflow_id}", response_model=ReportResponse)
async def get_report(workflow_id: str) -> ReportResponse:
    """Retrieve the generated report for a completed workflow."""
    state = await get_state(workflow_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

    if state.get("status") not in ("completed", "failed"):
        raise HTTPException(status_code=202, detail="Report not yet available — workflow still running")

    return ReportResponse(
        workflow_id=workflow_id,
        report_markdown=state.get("report_markdown"),
        pdf_url=f"/report/{workflow_id}/pdf" if state.get("pdf_path") else None,
        drive_url=state.get("drive_url"),
        generated_at=_parse_dt(state.get("completed_at")),
    )


@router.get("/report/{workflow_id}/pdf")
async def download_report_pdf(workflow_id: str) -> FileResponse:
    """Download the generated PDF for a workflow."""
    state = await get_state(workflow_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

    pdf_path = state.get("pdf_path")
    if not pdf_path or not Path(pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF not found")

    company = state.get("lead_company", "Report")
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in company)
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"Business_Audit_{safe_name}.pdf",
    )


@router.get("/logs/{workflow_id}")
async def get_workflow_logs(workflow_id: str) -> dict:
    """Retrieve structured execution logs for a workflow."""
    state = await get_state(workflow_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

    return {
        "workflow_id": workflow_id,
        "log_entries": state.get("log_entries", []),
        "nodes_completed": state.get("nodes_completed", []),
        "status": state.get("status"),
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
    }


@router.get("/workflows")
async def list_workflows() -> dict:
    """List all workflow IDs and their statuses."""
    ids = await list_workflow_ids()
    results = []
    for wid in ids:
        state = await get_state(wid)
        if state:
            results.append({
                "workflow_id": wid,
                "status": state.get("status", "unknown"),
                "company": state.get("lead_company", ""),
                "email": state.get("lead_email", ""),
                "progress_pct": state.get("progress_pct", 0),
                "submitted_at": state.get("submitted_at"),
            })
    return {"workflows": results, "total": len(results)}


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.utcnow(),
    )


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
