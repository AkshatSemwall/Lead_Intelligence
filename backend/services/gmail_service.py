"""
Gmail API service for sending emails with PDF attachments.
Uses OAuth2 refresh token flow — no user interaction required at runtime.
"""
from __future__ import annotations

import base64
import logging
import mimetypes
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _build_gmail_service(settings: Any):
    """Build an authenticated Gmail API service object."""
    from google.oauth2.credentials import Credentials  # type: ignore
    from googleapiclient.discovery import build  # type: ignore

    creds = Credentials(
        token=None,
        refresh_token=settings.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


class GmailService:
    def __init__(self, settings: Any | None = None) -> None:
        from backend.config import get_settings

        self._settings = settings or get_settings()
        self._service: Any = None

    def _get_service(self) -> Any:
        if self._service is None:
            self._service = _build_gmail_service(self._settings)
        return self._service

    def _build_message(
        self,
        to: str,
        subject: str,
        html_body: str,
        attachment_path: str | None = None,
    ) -> dict:
        msg = MIMEMultipart("mixed")
        msg["To"] = to
        msg["From"] = self._settings.gmail_sender_email
        msg["Subject"] = subject

        # HTML body
        alternative = MIMEMultipart("alternative")
        alternative.attach(MIMEText(html_body, "html", "utf-8"))
        msg.attach(alternative)

        # PDF attachment
        if attachment_path and Path(attachment_path).exists():
            with open(attachment_path, "rb") as f:
                pdf_data = f.read()
            attachment = MIMEApplication(pdf_data, _subtype="pdf")
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=Path(attachment_path).name,
            )
            msg.attach(attachment)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        return {"raw": raw}

    async def send_report_email(
        self,
        to_email: str,
        lead_name: str,
        company_name: str,
        pdf_path: str | None,
        drive_url: str | None = None,
    ) -> bool:
        """
        Send the audit report email with PDF attachment.
        Returns True on success, False on failure.
        """
        import asyncio
        import functools

        html_body = _build_email_html(lead_name, company_name, drive_url)
        subject = f"Your Business Audit Report — {company_name} | Lead Intelligence"

        message = self._build_message(
            to=to_email,
            subject=subject,
            html_body=html_body,
            attachment_path=pdf_path,
        )

        service = self._get_service()
        loop = asyncio.get_event_loop()

        try:
            await loop.run_in_executor(
                None,
                functools.partial(
                    service.users().messages().send(userId="me", body=message).execute
                ),
            )
            logger.info("Report email sent to %s", to_email)
            return True
        except Exception as exc:
            logger.error("Gmail send failed: %s", exc)
            return False


def _build_email_html(lead_name: str, company_name: str, drive_url: str | None) -> str:
    drive_btn = ""
    if drive_url:
        drive_btn = f"""
        <div style="margin-top:20px;">
            <a href="{drive_url}" style="background:#0ea5e9;color:white;padding:12px 28px;
               border-radius:6px;text-decoration:none;font-weight:600;display:inline-block;">
                View Report in Google Drive
            </a>
        </div>"""

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background:#f8fafc; margin:0; padding:0; }}
    .container {{ max-width:600px; margin:40px auto; background:white;
                  border-radius:12px; overflow:hidden; box-shadow:0 4px 20px rgba(0,0,0,.08); }}
    .header {{ background:linear-gradient(135deg,#0f172a,#1e3a5f); padding:40px 40px 30px;
               text-align:center; }}
    .header h1 {{ color:white; font-size:24px; margin:0 0 8px; }}
    .header p {{ color:#94a3b8; margin:0; font-size:14px; }}
    .body {{ padding:40px; }}
    .body p {{ color:#475569; line-height:1.7; margin:0 0 16px; }}
    .highlight {{ background:#f0f9ff; border-left:4px solid #0ea5e9; padding:16px 20px;
                  border-radius:0 8px 8px 0; margin:20px 0; color:#0c4a6e; }}
    .footer {{ background:#f1f5f9; padding:20px 40px; text-align:center;
               font-size:12px; color:#94a3b8; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Your Business Audit Report is Ready</h1>
      <p>Powered by Lead Intelligence AI</p>
    </div>
    <div class="body">
      <p>Hi {lead_name},</p>
      <p>Thank you for reaching out! We've completed a comprehensive AI-powered audit of
         <strong>{company_name}</strong> and your personalised report is attached to this email.</p>
      <div class="highlight">
        Your report includes:
        <ul style="margin:8px 0 0 16px; padding:0;">
          <li>Executive Summary</li>
          <li>Company Overview & Industry Analysis</li>
          <li>Website Audit</li>
          <li>AI &amp; Automation Opportunities</li>
          <li>Strategic Recommendations</li>
          <li>Prioritised Next Steps</li>
        </ul>
      </div>
      <p>Please find the full report attached as a PDF. If you have any questions or would like
         to discuss the findings, feel free to reply to this email.</p>
      {drive_btn}
    </div>
    <div class="footer">
      <p>This report was generated automatically by Lead Intelligence AI.<br>
         &copy; 2025 Lead Intelligence. All rights reserved.</p>
    </div>
  </div>
</body>
</html>"""


_gmail_instance: GmailService | None = None


def get_gmail_service() -> GmailService:
    global _gmail_instance
    if _gmail_instance is None:
        _gmail_instance = GmailService()
    return _gmail_instance
