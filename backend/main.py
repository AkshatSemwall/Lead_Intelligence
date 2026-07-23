"""
FastAPI application entrypoint.
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router
from backend.config import get_settings
from backend.graph.workflow import get_workflow
from backend.utils.helpers import setup_logging
from backend.services.google_config import validate_google_credentials

settings = get_settings()
setup_logging(debug=settings.debug)
logger = logging.getLogger(__name__)
_request_counts: dict[str, list[float]] = defaultdict(list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-compile LangGraph on startup for faster first request."""
    logger.info("Starting Lead Intelligence backend…")
    try:
        get_workflow()  # compile graph
        validate_google_credentials()
        logger.info("LangGraph workflow compiled and ready")
    except Exception as exc:
        logger.error("Failed to compile LangGraph workflow: %s", exc)
    yield
    logger.info("Lead Intelligence backend shutting down")


app = FastAPI(
    title="Lead Intelligence API",
    description="Autonomous multi-agent lead research and report generation system",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    headers = getattr(request, "headers", {})
    request_id = headers.get("x-request-id") if hasattr(headers, "get") else None
    if not request_id:
        request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    if settings.api_key:
        provided_key = headers.get("x-api-key") if hasattr(headers, "get") else None
        bearer = None
        auth_header = headers.get("authorization") if hasattr(headers, "get") else None
        if auth_header and auth_header.lower().startswith("bearer "):
            bearer = auth_header[7:].strip()
        if provided_key != settings.api_key and bearer != settings.api_key:
            response = JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            response.headers["x-request-id"] = request_id
            response.headers["www-authenticate"] = 'Bearer realm="api"'
            return response

    client_key = headers.get("x-forwarded-for") or headers.get("x-real-ip") or "anonymous"
    now = time.monotonic()
    bucket = _request_counts[str(client_key)]
    bucket[:] = [ts for ts in bucket if now - ts < settings.rate_limit_window_seconds]
    if len(bucket) >= settings.rate_limit_requests:
        response = JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        response.headers["x-request-id"] = request_id
        response.headers["retry-after"] = str(settings.rate_limit_window_seconds)
        return response
    bucket.append(now)

    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    response.headers["x-content-type-options"] = "nosniff"
    response.headers["x-frame-options"] = "DENY"
    response.headers["referrer-policy"] = "strict-origin-when-cross-origin"
    response.headers["x-ratelimit-limit"] = str(settings.rate_limit_requests)
    response.headers["x-ratelimit-remaining"] = str(max(0, settings.rate_limit_requests - len(bucket)))
    return response

# API routes
app.include_router(router, prefix="/api")

# Serve generated PDFs statically
if os.path.exists("generated_pdfs"):
    app.mount("/pdfs", StaticFiles(directory="generated_pdfs"), name="pdfs")


# SPA Static Files & Fallback Handler for React Router
if os.path.exists("frontend/dist"):
    # First serve static assets like CSS/JS from frontend/dist/assets
    assets_dir = os.path.join("frontend", "dist", "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # Catch-all route for SPA client routing (/dashboard, /status, /report, etc.)
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # Don't intercept API or static files
        target = os.path.join("frontend", "dist", full_path)
        if os.path.exists(target) and os.path.isfile(target):
            return FileResponse(target)
        return FileResponse(os.path.join("frontend", "dist", "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "name": "Lead Intelligence API",
            "version": "1.0.0",
            "docs": "/api/docs",
        }
