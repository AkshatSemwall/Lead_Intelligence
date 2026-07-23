"""
LangGraph workflow definition.
Implements the full 12-node pipeline with retry logic, conditional transitions,
and execution tracking.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Literal

from langgraph.graph import StateGraph, END  # type: ignore

from backend.models.state import WorkflowState
from backend.agents.validation import validation_node
from backend.agents.company_research import company_research_node
from backend.agents.business_analysis import business_analysis_node
from backend.agents.insight_generation import insight_generation_node
from backend.agents.report_generation import report_generation_node
from backend.agents.pdf_generation import pdf_generation_node
from backend.agents.email_agent import email_node
from backend.agents.logging_agent import logging_node
from backend.agents.sheets_agent import sheets_node
from backend.agents.drive_agent import drive_node
from backend.utils.helpers import make_log_entry, now_iso, compute_progress, retry_async
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ─── Wrapped nodes with retry logic ──────────────────────────────────────────


def _wrap_with_retry(node_fn, node_name: str, max_retries: int = 2):
    """Wrap a node function with retry logic and execution tracking."""

    async def wrapped(state: WorkflowState) -> WorkflowState:
        retry_counts = dict(state.get("retry_counts", {}))

        async def attempt():
            return await node_fn(state)

        try:
            new_state = await retry_async(attempt, max_retries=max_retries, delay=settings.retry_delay_seconds)
            retry_counts[node_name] = retry_counts.get(node_name, 0)
            return {**new_state, "retry_counts": retry_counts}
        except Exception as exc:
            retry_counts[node_name] = max_retries
            log_entries = list(state.get("log_entries", []))
            log_entries.append(make_log_entry(node_name, "exhausted_retries", str(exc), error=str(exc)))
            return {**state, "retry_counts": retry_counts, "log_entries": log_entries}

    wrapped.__name__ = node_name
    return wrapped


# ─── Orchestrator entry node ──────────────────────────────────────────────────


async def orchestrator_node(state: WorkflowState) -> WorkflowState:
    """Orchestrator: initialises workflow state and tracking fields."""
    log_entries = list(state.get("log_entries", []))
    log_entries.append(make_log_entry("orchestrator", "started", "Workflow started"))

    return {
        **state,
        "status": "running",
        "current_node": "orchestrator",
        "nodes_completed": [],
        "log_entries": log_entries,
        "retry_counts": {},
        "email_sent": False,
        "started_at": now_iso(),
        "progress_pct": 0,
    }


# ─── Finaliser node ───────────────────────────────────────────────────────────


async def finalise_node(state: WorkflowState) -> WorkflowState:
    """Mark workflow as completed and compute final progress."""
    log_entries = list(state.get("log_entries", []))
    log_entries.append(make_log_entry("orchestrator", "completed", "Workflow completed"))

    nodes_completed = list(state.get("nodes_completed", []))
    progress = compute_progress(nodes_completed)

    return {
        **state,
        "status": "completed",
        "current_node": "done",
        "completed_at": now_iso(),
        "log_entries": log_entries,
        "progress_pct": progress,
    }


# ─── Conditional edge functions ────────────────────────────────────────────────


def route_after_validation(state: WorkflowState) -> Literal["company_research", "end_failed"]:
    validation = state.get("validation") or {}
    if validation.get("is_valid") and not validation.get("is_duplicate"):
        return "company_research"
    return "end_failed"


def should_continue_after_pdf(state: WorkflowState) -> Literal["drive", "email"]:
    """Upload to Drive first (we need the URL for the email), then email."""
    if state.get("pdf_path"):
        return "drive"
    return "email"


async def end_failed_node(state: WorkflowState) -> WorkflowState:
    """Terminal node for validation failures."""
    log_entries = list(state.get("log_entries", []))
    validation = state.get("validation") or {}
    errors = validation.get("errors", ["Validation failed"])
    log_entries.append(make_log_entry("orchestrator", "failed", f"Workflow terminated: {errors}"))

    return {
        **state,
        "status": "failed",
        "error": "; ".join(errors),
        "current_node": "failed",
        "completed_at": now_iso(),
        "log_entries": log_entries,
    }


# ─── Graph construction ────────────────────────────────────────────────────────


def build_workflow() -> Any:
    """Build and compile the LangGraph StateGraph."""
    graph = StateGraph(WorkflowState)

    # Register nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("validation", validation_node)
    graph.add_node("company_research", company_research_node)
    graph.add_node("business_analysis", business_analysis_node)
    graph.add_node("insight_generation", insight_generation_node)
    graph.add_node("report_generation", report_generation_node)
    graph.add_node("pdf_generation", pdf_generation_node)
    graph.add_node("drive", drive_node)
    graph.add_node("email", email_node)
    graph.add_node("logging", logging_node)
    graph.add_node("sheets", sheets_node)
    graph.add_node("finalise", finalise_node)
    graph.add_node("end_failed", end_failed_node)

    # Entry point
    graph.set_entry_point("orchestrator")

    # Linear transitions
    graph.add_edge("orchestrator", "validation")

    # Conditional: validation can proceed or fail
    graph.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "company_research": "company_research",
            "end_failed": "end_failed",
        },
    )

    # Research → Analysis → Insights → Report → PDF
    graph.add_edge("company_research", "business_analysis")
    graph.add_edge("business_analysis", "insight_generation")
    graph.add_edge("insight_generation", "report_generation")
    graph.add_edge("report_generation", "pdf_generation")

    # PDF → Drive (to get URL) → Email → Logging → Sheets → Finalise
    graph.add_conditional_edges(
        "pdf_generation",
        should_continue_after_pdf,
        {
            "drive": "drive",
            "email": "email",
        },
    )
    graph.add_edge("drive", "email")
    graph.add_edge("email", "logging")
    graph.add_edge("logging", "sheets")
    graph.add_edge("sheets", "finalise")

    # Terminal edges
    graph.add_edge("finalise", END)
    graph.add_edge("end_failed", END)

    return graph.compile()


# Module-level compiled graph (lazy)
_compiled_graph: Any = None


def get_workflow() -> Any:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_workflow()
        logger.info("LangGraph workflow compiled successfully")
    return _compiled_graph
