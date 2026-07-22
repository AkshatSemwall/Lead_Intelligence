"""
Google Sheets API service for logging lead and workflow data.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

SHEET_HEADERS = [
    "Workflow ID",
    "Timestamp",
    "Lead Name",
    "Lead Email",
    "Company",
    "Website",
    "Status",
    "Email Sent",
    "Drive URL",
    "Report Generated",
    "Error",
]


def _build_sheets_service(settings: Any):
    from google.oauth2.credentials import Credentials  # type: ignore
    from googleapiclient.discovery import build  # type: ignore

    creds = Credentials(
        token=None,
        refresh_token=settings.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


class SheetsService:
    def __init__(self, settings: Any | None = None) -> None:
        from backend.config import get_settings

        self._settings = settings or get_settings()
        self._service: Any = None

    def _get_service(self) -> Any:
        if self._service is None:
            self._service = _build_sheets_service(self._settings)
        return self._service

    async def ensure_header_row(self) -> None:
        """Ensure the first row contains the column headers."""
        import asyncio
        import functools

        service = self._get_service()
        sheet_id = self._settings.google_sheet_id
        loop = asyncio.get_event_loop()

        try:
            result = await loop.run_in_executor(
                None,
                functools.partial(
                    service.spreadsheets()
                    .values()
                    .get(spreadsheetId=sheet_id, range="Sheet1!A1:K1")
                    .execute
                ),
            )
            values = result.get("values", [])
            if not values:
                await loop.run_in_executor(
                    None,
                    functools.partial(
                        service.spreadsheets()
                        .values()
                        .update(
                            spreadsheetId=sheet_id,
                            range="Sheet1!A1",
                            valueInputOption="RAW",
                            body={"values": [SHEET_HEADERS]},
                        )
                        .execute
                    ),
                )
        except Exception as exc:
            logger.warning("Could not ensure sheet header: %s", exc)

    async def append_lead_row(
        self,
        workflow_id: str,
        lead_name: str,
        lead_email: str,
        company: str,
        website: str,
        status: str,
        email_sent: bool,
        drive_url: str | None,
        report_generated: bool,
        error: str | None,
    ) -> str | None:
        """
        Append a lead record row. Returns the range string of the inserted row.
        """
        import asyncio
        import functools

        service = self._get_service()
        sheet_id = self._settings.google_sheet_id
        loop = asyncio.get_event_loop()

        row = [
            workflow_id,
            datetime.utcnow().isoformat(),
            lead_name,
            lead_email,
            company,
            website,
            status,
            "Yes" if email_sent else "No",
            drive_url or "",
            "Yes" if report_generated else "No",
            error or "",
        ]

        try:
            result = await loop.run_in_executor(
                None,
                functools.partial(
                    service.spreadsheets()
                    .values()
                    .append(
                        spreadsheetId=sheet_id,
                        range="Sheet1!A:K",
                        valueInputOption="RAW",
                        insertDataOption="INSERT_ROWS",
                        body={"values": [row]},
                    )
                    .execute
                ),
            )
            updated_range = result.get("updates", {}).get("updatedRange", "")
            logger.info("Sheets row appended: %s", updated_range)
            return updated_range
        except Exception as exc:
            logger.error("Sheets append failed: %s", exc)
            return None

    async def update_status(
        self,
        row_range: str,
        status: str,
        email_sent: bool | None = None,
        drive_url: str | None = None,
        error: str | None = None,
    ) -> None:
        """Update status columns for an existing row."""
        import asyncio
        import functools

        service = self._get_service()
        sheet_id = self._settings.google_sheet_id
        loop = asyncio.get_event_loop()

        # Parse row number from range like "Sheet1!A5:K5"
        try:
            row_num = int(row_range.split("!")[1].split(":")[0][1:])
        except Exception:
            logger.warning("Could not parse row number from range: %s", row_range)
            return

        updates: list[dict] = []

        # Status column G (index 7)
        updates.append({
            "range": f"Sheet1!G{row_num}",
            "values": [[status]],
        })
        if email_sent is not None:
            updates.append({"range": f"Sheet1!H{row_num}", "values": [["Yes" if email_sent else "No"]]})
        if drive_url is not None:
            updates.append({"range": f"Sheet1!I{row_num}", "values": [[drive_url]]})
        if error is not None:
            updates.append({"range": f"Sheet1!K{row_num}", "values": [[error]]})

        try:
            await loop.run_in_executor(
                None,
                functools.partial(
                    service.spreadsheets()
                    .values()
                    .batchUpdate(
                        spreadsheetId=sheet_id,
                        body={"valueInputOption": "RAW", "data": updates},
                    )
                    .execute
                ),
            )
        except Exception as exc:
            logger.error("Sheets update failed: %s", exc)


_sheets_instance: SheetsService | None = None


def get_sheets_service() -> SheetsService:
    global _sheets_instance
    if _sheets_instance is None:
        _sheets_instance = SheetsService()
    return _sheets_instance
