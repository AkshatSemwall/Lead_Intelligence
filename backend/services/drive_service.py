"""
Google Drive API service for uploading generated PDFs.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _build_drive_service(settings: Any):
    from google.oauth2.credentials import Credentials  # type: ignore
    from googleapiclient.discovery import build  # type: ignore

    creds = Credentials(
        token=None,
        refresh_token=settings.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


class DriveService:
    def __init__(self, settings: Any | None = None) -> None:
        from backend.config import get_settings

        self._settings = settings or get_settings()
        self._service: Any = None

    def _get_service(self) -> Any:
        if self._service is None:
            self._service = _build_drive_service(self._settings)
        return self._service

    async def upload_pdf(
        self,
        pdf_path: str,
        company_name: str,
        workflow_id: str,
    ) -> tuple[str | None, str | None]:
        """
        Upload the PDF to the configured Google Drive folder.
        Returns (file_id, shareable_url) or (None, None) on failure.
        """
        import asyncio
        import functools

        from googleapiclient.http import MediaFileUpload  # type: ignore

        service = self._get_service()
        folder_id = self._settings.google_drive_folder_id
        loop = asyncio.get_event_loop()

        if not Path(pdf_path).exists():
            logger.error("PDF not found at path: %s", pdf_path)
            return None, None

        filename = f"Business_Audit_{company_name}_{workflow_id[:8]}.pdf"
        file_metadata: dict = {"name": filename, "mimeType": "application/pdf"}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        media = MediaFileUpload(pdf_path, mimetype="application/pdf", resumable=True)

        try:
            # Upload
            uploaded = await loop.run_in_executor(
                None,
                functools.partial(
                    service.files()
                    .create(body=file_metadata, media_body=media, fields="id")
                    .execute
                ),
            )
            file_id = uploaded.get("id")
            if not file_id:
                return None, None

            # Make publicly viewable
            await loop.run_in_executor(
                None,
                functools.partial(
                    service.permissions()
                    .create(
                        fileId=file_id,
                        body={"type": "anyone", "role": "reader"},
                    )
                    .execute
                ),
            )

            drive_url = f"https://drive.google.com/file/d/{file_id}/view"
            logger.info("PDF uploaded to Drive: %s", drive_url)
            return file_id, drive_url

        except Exception as exc:
            logger.error("Drive upload failed: %s", exc)
            return None, None


_drive_instance: DriveService | None = None


def get_drive_service() -> DriveService:
    global _drive_instance
    if _drive_instance is None:
        _drive_instance = DriveService()
    return _drive_instance
