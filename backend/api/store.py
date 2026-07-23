"""
In-memory workflow state store.
In production, replace with Redis or a database-backed store.
"""
from __future__ import annotations

import asyncio
from typing import Optional

from backend.models.state import WorkflowState

# Workflow states keyed by workflow_id
_store: dict[str, WorkflowState] = {}
_lock = asyncio.Lock()


async def save_state(workflow_id: str, state: WorkflowState) -> None:
    async with _lock:
        _store[workflow_id] = state


async def get_state(workflow_id: str) -> Optional[WorkflowState]:
    async with _lock:
        return _store.get(workflow_id)


async def list_workflow_ids() -> list[str]:
    async with _lock:
        return list(_store.keys())


def get_store() -> dict[str, WorkflowState]:
    return _store
