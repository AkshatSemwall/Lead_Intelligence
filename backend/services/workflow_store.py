"""Durable workflow persistence backed by JSON files on disk."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

from backend.models.state import WorkflowState


class JsonFileWorkflowStore:
    """Persist workflow states to JSON files so they survive restarts."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self._base_dir = Path(base_dir or "workflow_state")
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    def _state_path(self, workflow_id: str) -> Path:
        return self._base_dir / f"{workflow_id}.json"

    async def save_state(self, workflow_id: str, state: WorkflowState) -> None:
        async with self._lock:
            path = self._state_path(workflow_id)
            path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")

    async def get_state(self, workflow_id: str) -> Optional[WorkflowState]:
        async with self._lock:
            path = self._state_path(workflow_id)
            if not path.exists():
                return None
            data = json.loads(path.read_text(encoding="utf-8"))
            return data

    async def list_workflow_ids(self) -> list[str]:
        async with self._lock:
            return sorted(p.stem for p in self._base_dir.glob("*.json") if p.is_file())


_store: JsonFileWorkflowStore | None = None


def get_workflow_store() -> JsonFileWorkflowStore:
    global _store
    if _store is None:
        _store = JsonFileWorkflowStore()
    return _store
