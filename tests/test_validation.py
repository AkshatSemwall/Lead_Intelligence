import asyncio

from backend.agents.validation import validation_node


def test_validation_accepts_realistic_sample_submission() -> None:
    state = {
        "lead_name": "Ava",
        "lead_email": "ava@example.com",
        "lead_company": "Northwind Labs",
        "lead_website": "https://northwindlabs.com",
        "log_entries": [],
        "nodes_completed": [],
    }

    result = asyncio.run(validation_node(state))

    assert result["validation"]["is_valid"] is True
    assert result["validation"]["is_duplicate"] is False
    assert result["validation"]["errors"] == []
