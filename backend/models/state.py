"""
Pydantic models: WorkflowState (LangGraph), API request/response models.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional
from typing_extensions import TypedDict

from pydantic import BaseModel, EmailStr, HttpUrl, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Lead / API models
# ─────────────────────────────────────────────────────────────────────────────


class LeadSubmissionRequest(BaseModel):
    name: str
    email: EmailStr
    company: str
    website: str
    phone: Optional[str] = None
    message: Optional[str] = None

    @field_validator("website")
    @classmethod
    def normalise_website(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        return v


class LeadSubmissionResponse(BaseModel):
    workflow_id: str
    status: str
    message: str
    submitted_at: datetime


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    status: str  # pending | running | completed | failed
    current_node: Optional[str]
    progress_pct: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]
    nodes_completed: list[str]


class ReportResponse(BaseModel):
    workflow_id: str
    report_markdown: Optional[str]
    pdf_url: Optional[str]
    drive_url: Optional[str]
    generated_at: Optional[datetime]


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


# ─────────────────────────────────────────────────────────────────────────────
# Research / Analysis intermediate models
# ─────────────────────────────────────────────────────────────────────────────


class CompanyResearchData(BaseModel):
    company_name: str = ""
    website_url: str = ""
    industry: str = ""
    description: str = ""
    services: list[str] = []
    technology_stack: list[str] = []
    competitors: list[str] = []
    recent_news: list[str] = []
    linkedin_data: str = ""
    founded: Optional[str] = None
    employee_count: Optional[str] = None
    headquarters: Optional[str] = None
    raw_web_content: str = ""


class BusinessAnalysisData(BaseModel):
    business_model: str = ""
    target_audience: str = ""
    strengths: list[str] = []
    weaknesses: list[str] = []
    pain_points: list[str] = []
    ai_opportunities: list[str] = []
    market_position: str = ""
    revenue_model: str = ""


class InsightData(BaseModel):
    website_audit: dict[str, Any] = {}
    recommendations: list[str] = []
    automation_opportunities: list[str] = []
    business_improvements: list[str] = []
    priority_actions: list[str] = []
    estimated_impact: str = ""


class ValidationResult(BaseModel):
    is_valid: bool
    is_duplicate: bool
    errors: list[str] = []
    normalised_email: str = ""
    normalised_website: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# LangGraph State  (TypedDict so LangGraph can operate on it)
# ─────────────────────────────────────────────────────────────────────────────


class WorkflowState(TypedDict, total=False):
    # Identity
    workflow_id: str
    submitted_at: str  # ISO datetime string

    # Lead input
    lead_name: str
    lead_email: str
    lead_company: str
    lead_website: str
    lead_phone: str
    lead_message: str

    # Validation
    validation: Optional[dict]  # ValidationResult.model_dump()
    validation_error: Optional[str]

    # Research
    research: Optional[dict]  # CompanyResearchData.model_dump()
    research_error: Optional[str]

    # Analysis
    analysis: Optional[dict]  # BusinessAnalysisData.model_dump()
    analysis_error: Optional[str]

    # Insights
    insights: Optional[dict]  # InsightData.model_dump()
    insights_error: Optional[str]

    # Report
    report_markdown: Optional[str]
    report_error: Optional[str]

    # PDF
    pdf_path: Optional[str]
    pdf_error: Optional[str]

    # Email
    email_sent: bool
    email_error: Optional[str]

    # Logging
    log_entries: list[dict]

    # Sheets
    sheet_row_id: Optional[str]
    sheets_error: Optional[str]

    # Drive
    drive_url: Optional[str]
    drive_file_id: Optional[str]
    drive_error: Optional[str]

    # Execution tracking
    status: str  # pending | running | completed | failed
    current_node: Optional[str]
    nodes_completed: list[str]
    error: Optional[str]
    retry_counts: dict[str, int]
    started_at: Optional[str]
    completed_at: Optional[str]
    progress_pct: int
