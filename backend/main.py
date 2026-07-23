"""
FastAPI application entrypoint.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router
from backend.config import get_settings
from backend.graph.workflow import get_workflow
from backend.utils.helpers import setup_logging

settings = get_settings()
setup_logging(debug=settings.debug)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-compile LangGraph on startup for faster first request."""
    logger.info("Starting Lead Intelligence backend…")
    try:
        get_workflow()  # compile graph
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
    allow_methods=["*"],
    allow_headers=["*"],
)

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
