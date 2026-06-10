"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Runtime settings for external services and local paths."""

    gemini_api_key: str | None
    gemini_model: str
    gemini_timeout_seconds: float
    google_sheets_enabled: bool
    google_sheets_spreadsheet_id: str | None
    google_sheets_range: str
    google_sheets_timeout_seconds: float
    google_sheets_retries: int
    google_application_credentials_path: Path | None
    google_sheets_credentials_file: Path | None
    google_sheets_credentials_path: Path | None
    google_sheets_token_path: Path | None
    google_service_account_path: Path | None

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv_if_available()
        return cls(
            gemini_api_key=_env_str("GEMINI_API_KEY") or _env_str("GOOGLE_API_KEY"),
            gemini_model=_env_str("GEMINI_MODEL", "gemini-2.5-flash"),
            gemini_timeout_seconds=_env_float("GEMINI_TIMEOUT_SECONDS", 30.0),
            google_sheets_enabled=_env_bool("GOOGLE_SHEETS_ENABLED", default=False),
            google_sheets_spreadsheet_id=_normalize_spreadsheet_id(_env_str("GOOGLE_SHEETS_SPREADSHEET_ID")),
            google_sheets_range=_env_str("GOOGLE_SHEETS_RANGE", "ProjectVault!A:I"),
            google_sheets_timeout_seconds=_env_float("GOOGLE_SHEETS_TIMEOUT_SECONDS", 60.0),
            google_sheets_retries=_env_int("GOOGLE_SHEETS_RETRIES", 2),
            google_application_credentials_path=_optional_path("GOOGLE_APPLICATION_CREDENTIALS"),
            google_sheets_credentials_file=_optional_path("GOOGLE_SHEETS_CREDENTIALS_FILE"),
            google_sheets_credentials_path=_optional_path("GOOGLE_SHEETS_CREDENTIALS_PATH"),
            google_sheets_token_path=_optional_path("GOOGLE_SHEETS_TOKEN_PATH"),
            google_service_account_path=_optional_path("GOOGLE_SERVICE_ACCOUNT_PATH"),
        )

    @property
    def google_sheets_service_account_path(self) -> Path | None:
        return (
            self.google_sheets_credentials_file
            or self.google_service_account_path
            or self.google_sheets_credentials_path
            or self.google_application_credentials_path
        )


def _optional_path(env_name: str) -> Path | None:
    value = _env_str(env_name)
    return Path(value).expanduser() if value else None


def _env_str(env_name: str, default: str | None = None) -> str | None:
    value = os.getenv(env_name)
    if value is None or not value.strip():
        return default
    return value.strip()


def _env_bool(env_name: str, default: bool = False) -> bool:
    value = os.getenv(env_name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_float(env_name: str, default: float) -> float:
    value = _env_str(env_name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_int(env_name: str, default: int) -> int:
    value = _env_str(env_name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _normalize_spreadsheet_id(value: str | None) -> str | None:
    if value is None:
        return None
    match = re.search(r"/spreadsheets/d/([^/]+)", value)
    if match:
        return match.group(1)
    return value.split("/edit", 1)[0].split("#", 1)[0].split("?", 1)[0].strip()


def load_dotenv_if_available() -> None:
    if _env_bool("PROJECTVAULT_SKIP_DOTENV", default=False):
        return

    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv()
