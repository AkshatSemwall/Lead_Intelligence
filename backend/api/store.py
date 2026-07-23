"""Workflow state persistence helpers."""
from __future__ import annotations

from typing import Optional

from backend.models.state import WorkflowState
from backend.services.workflow_store import get_workflow_store


async def save_state(workflow_id: str, state: WorkflowState) -> None:
    store = get_workflow_store()
    await store.save_state(workflow_id, state)


async def get_state(workflow_id: str) -> Optional[WorkflowState]:
    store = get_workflow_store()
    return await store.get_state(workflow_id)


async def list_workflow_ids() -> list[str]:
    store = get_workflow_store()
    return await store.list_workflow_ids()


def get_store() -> dict[str, WorkflowState]:
    return {}
