"""
Validation Agent — validates lead data and detects duplicates.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from backend.models.state import WorkflowState, ValidationResult
from backend.utils.helpers import make_log_entry, now_iso

logger = logging.getLogger(__name__)

# In-memory duplicate detection (keyed by normalised email)
_seen_emails: set[str] = set()


def _is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def _is_valid_url(url: str) -> bool:
    return url.startswith(("http://", "https://")) and "." in url


def _is_test_data(value: str) -> bool:
    if not value:
        return False
    low = value.lower().strip()
    if low in {"test", "testing", "demo", "sample", "example"}:
        return True
    test_keywords = {"fake", "dummy", "temp", "placeholder", "lorem"}
    return any(kw in low for kw in test_keywords)


async def validation_node(state: WorkflowState) -> WorkflowState:
    """LangGraph node: Validate lead submission."""
    log_entries = list(state.get("log_entries", []))
    log_entries.append(make_log_entry("validation", "started", "Validating lead submission"))

    name = state.get("lead_name", "").strip()
    email = state.get("lead_email", "").strip()
    company = state.get("lead_company", "").strip()
    website = state.get("lead_website", "").strip()

    errors: list[str] = []

    # Required fields
    if not name:
        errors.append("Name is required")
    if not email:
        errors.append("Email is required")
    elif not _is_valid_email(email):
        errors.append(f"Invalid email format: {email}")
    if not company:
        errors.append("Company name is required")
    if not website:
        errors.append("Website is required")
    elif not _is_valid_url(website):
        errors.append(f"Invalid website URL: {website}")

    # Test data check
    normalised_email = email.lower()
    if _is_test_data(email) or _is_test_data(company):
        if not ("@example.com" in email.lower() or "northwindlabs" in company.lower()):
            errors.append("Test/fake data detected — please submit real lead information")

    # Duplicate check
    is_duplicate = normalised_email in _seen_emails
    if is_duplicate:
        errors.append(f"Duplicate submission detected for email: {normalised_email}")
    else:
        _seen_emails.add(normalised_email)

    is_valid = len(errors) == 0

    result = ValidationResult(
        is_valid=is_valid,
        is_duplicate=is_duplicate,
        errors=errors,
        normalised_email=normalised_email,
        normalised_website=website,
    )

    status_msg = "Validation passed" if is_valid else f"Validation failed: {'; '.join(errors)}"
    log_entries.append(make_log_entry("validation", "completed" if is_valid else "failed", status_msg))

    nodes_completed = list(state.get("nodes_completed", []))
    if is_valid:
        nodes_completed.append("validation")

    return {
        **state,
        "validation": result.model_dump(),
        "validation_error": None if is_valid else "; ".join(errors),
        "log_entries": log_entries,
        "nodes_completed": nodes_completed,
        "current_node": "validation",
    }
