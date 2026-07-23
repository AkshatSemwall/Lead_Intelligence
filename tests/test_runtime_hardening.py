import asyncio
from types import SimpleNamespace

from fastapi.responses import Response
from fastapi.testclient import TestClient

from backend.config import get_settings
from backend.main import add_request_context, app, _request_counts


client = TestClient(app)


def test_request_context_sets_security_headers_and_request_id() -> None:
    async def call_next(request):
        return Response(status_code=200)

    request = SimpleNamespace(
        headers={},
        state=SimpleNamespace(),
    )

    response = asyncio.run(add_request_context(request, call_next))

    assert response.headers["x-request-id"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert request.state.request_id


def test_api_key_enforcement_when_configured() -> None:
    settings = get_settings()
    original_key = settings.api_key
    settings.api_key = "secret"
    try:
        response = client.get("/api/health", headers={"x-api-key": "wrong"})
        assert response.status_code == 401
    finally:
        settings.api_key = original_key


def test_rate_limiting_returns_429() -> None:
    settings = get_settings()
    original_limit = settings.rate_limit_requests
    original_window = settings.rate_limit_window_seconds
    settings.rate_limit_requests = 1
    settings.rate_limit_window_seconds = 60
    _request_counts.clear()
    try:
        first = client.get("/api/health")
        second = client.get("/api/health")
        assert first.status_code == 200
        assert second.status_code == 429
    finally:
        settings.rate_limit_requests = original_limit
        settings.rate_limit_window_seconds = original_window
        _request_counts.clear()
