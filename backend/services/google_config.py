"""Google credential validation helpers."""
from __future__ import annotations

import logging
from backend.config import get_settings

logger = logging.getLogger(__name__)


def validate_google_credentials() -> None:
    settings = get_settings()
    missing = []
    if not settings.google_client_id:
        missing.append("GOOGLE_CLIENT_ID")
    if not settings.google_client_secret:
        missing.append("GOOGLE_CLIENT_SECRET")
    if not settings.google_refresh_token:
        missing.append("GOOGLE_REFRESH_TOKEN")
    if not settings.google_sheet_id:
        missing.append("GOOGLE_SHEET_ID")
    if not settings.google_drive_folder_id:
        missing.append("GOOGLE_DRIVE_FOLDER_ID")
    if not settings.gmail_sender_email:
        missing.append("GMAIL_SENDER_EMAIL")
    if missing:
        logger.warning("Google credentials missing: %s", ", ".join(missing))
        return
    logger.info("Google credential configuration detected")
