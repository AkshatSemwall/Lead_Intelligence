"""Generate a Google OAuth refresh token for Gmail, Sheets, and Drive access."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


def getenv(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def load_environment() -> None:
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH)


def prompt_env(name: str, prompt_text: str) -> str:
    value = getenv(name)
    if value:
        return value
    return input(f"{prompt_text}: ").strip()


def build_client_config(client_id: str, client_secret: str) -> dict[str, Any]:
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def main() -> None:
    load_environment()

    print("Google OAuth Refresh Token Generator")
    print("-------------------------------------")

    client_id = prompt_env("GOOGLE_CLIENT_ID", "Enter your Google OAuth Client ID")
    client_secret = prompt_env("GOOGLE_CLIENT_SECRET", "Enter your Google OAuth Client Secret")

    if not client_id or not client_secret:
        raise SystemExit("Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET.")

    flow = InstalledAppFlow.from_client_config(build_client_config(client_id, client_secret), SCOPES)
    creds = flow.run_local_server(port=0)

    print("\nCopy this value into your .env file:")
    print("GOOGLE_REFRESH_TOKEN=", creds.refresh_token)
    print("\nRecommended scopes:")
    for scope in SCOPES:
        print(f"  - {scope}")

    print("\nIf the refresh token is blank, re-run with prompt=consent in the OAuth request.")


if __name__ == "__main__":
    main()
