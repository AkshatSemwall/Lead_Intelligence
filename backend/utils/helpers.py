"""
Shared utilities: JSON parsing, retry helpers, structured logging.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ─── JSON parsing ─────────────────────────────────────────────────────────────


def extract_json(text: str) -> dict | None:
    """
    Robustly extract JSON from LLM output that may contain markdown fences or prose.
    """
    # Try raw parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences
    cleaned = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip().rstrip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Find first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    logger.warning("Could not extract JSON from LLM response (length=%d)", len(text))
    return None


# ─── Retry helper ─────────────────────────────────────────────────────────────


async def retry_async(
    fn: Callable,
    max_retries: int = 3,
    delay: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Any:
    """
    Retry an async callable up to max_retries times with exponential back-off.
    """
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return await fn()
        except exceptions as exc:
            last_exc = exc
            wait = delay * (2 ** (attempt - 1))
            logger.warning("Attempt %d/%d failed (%s). Retrying in %.1fs…", attempt, max_retries, exc, wait)
            if attempt < max_retries:
                await asyncio.sleep(wait)
    raise last_exc  # type: ignore


# ─── Progress tracking ────────────────────────────────────────────────────────

NODE_WEIGHTS: dict[str, int] = {
    "validation": 5,
    "company_research": 20,
    "business_analysis": 15,
    "insight_generation": 15,
    "report_generation": 15,
    "pdf_generation": 10,
    "email": 5,
    "logging": 5,
    "sheets": 5,
    "drive": 5,
}

TOTAL_WEIGHT = sum(NODE_WEIGHTS.values())


def compute_progress(nodes_completed: list[str]) -> int:
    done = sum(NODE_WEIGHTS.get(n, 0) for n in nodes_completed)
    return min(100, int(done / TOTAL_WEIGHT * 100))


# ─── Structured logging ───────────────────────────────────────────────────────


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    # Quiet noisy libraries
    for lib in ("httpx", "httpcore", "googleapiclient", "urllib3"):
        logging.getLogger(lib).setLevel(logging.WARNING)


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def make_log_entry(node: str, status: str, message: str, error: str | None = None) -> dict:
    return {
        "timestamp": now_iso(),
        "node": node,
        "status": status,
        "message": message,
        "error": error,
    }
