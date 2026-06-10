from __future__ import annotations

import json

from app.config import Settings
from app.extractors.gemini_extractor import GeminiExtractor, analyze_file, parse_analysis_json


def _settings(api_key: str | None = None) -> Settings:
    return Settings(
        gemini_api_key=api_key,
        gemini_model="gemini-test",
        gemini_timeout_seconds=30.0,
        google_sheets_enabled=False,
        google_sheets_spreadsheet_id=None,
        google_sheets_range="ProjectVault!A:I",
        google_sheets_timeout_seconds=60.0,
        google_sheets_retries=2,
        google_application_credentials_path=None,
        google_sheets_credentials_file=None,
        google_sheets_credentials_path=None,
        google_sheets_token_path=None,
        google_service_account_path=None,
    )


def _file_item(file_type: str = "assignment_notice") -> dict[str, object]:
    return {
        "path": "input_workspace/assignment/notice.txt",
        "filename": "notice.txt",
        "extension": ".txt",
        "file_type": file_type,
        "content": "Submit a report and include execution examples.",
        "content_preview": "Submit a report and include execution examples.",
        "warnings": [],
    }


def test_analyze_file_uses_fake_without_api_key(monkeypatch) -> None:
    monkeypatch.setenv("PROJECTVAULT_SKIP_DOTENV", "true")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    result = analyze_file(_file_item())

    assert result["file_path"] == "input_workspace/assignment/notice.txt"
    assert result["file_type"] == "assignment_notice"
    assert result["summary"].startswith("Fake analysis")
    assert result["tasks"][0]["priority"] == "HIGH"


def test_extractor_uses_fake_in_dry_run_even_with_api_key() -> None:
    extractor = GeminiExtractor(settings=_settings(api_key="test-key"), dry_run=True)

    result = extractor.analyze_file(_file_item("source_code"))

    assert result["summary"].startswith("Fake analysis")
    assert result["errors"][0]["title"] == "API 키 노출 가능성 점검"


def test_parse_analysis_json_accepts_json_fence() -> None:
    payload = {
        "file_path": "input_workspace/code/app.py",
        "file_type": "source_code",
        "summary": "Parses a Python script.",
        "concepts": [{"name": "CLI", "description": "Command line interface"}],
        "requirements": [],
        "tasks": [{"title": "Add tests", "priority": "HIGH", "reason": "Code has behavior"}],
        "errors": [],
        "decisions": [{"title": "Use argparse", "reason": "Standard library"}],
    }

    result = parse_analysis_json(f"```json\n{json.dumps(payload)}\n```", _file_item("source_code"))

    assert result["summary"] == "Parses a Python script."
    assert result["concepts"][0]["name"] == "CLI"
    assert result["tasks"][0]["title"] == "Add tests"


def test_parse_analysis_json_falls_back_on_invalid_json() -> None:
    result = parse_analysis_json("not json", _file_item("note"))

    assert result["summary"].startswith("Fallback analysis")
    assert result["file_type"] == "note"


def test_api_key_path_calls_gemini(monkeypatch) -> None:
    extractor = GeminiExtractor(settings=_settings(api_key="test-key"), dry_run=False)
    called = {"value": False}

    def fake_call(file_item: dict[str, object]) -> str:
        called["value"] = True
        return json.dumps(
            {
                "file_path": file_item["path"],
                "file_type": file_item["file_type"],
                "summary": "Real Gemini-shaped response.",
                "concepts": [],
                "requirements": [],
                "tasks": [],
                "errors": [],
                "decisions": [],
            }
        )

    monkeypatch.setattr(extractor, "_call_gemini", fake_call)

    result = extractor.analyze_file(_file_item("document"))

    assert called["value"] is True
    assert result["summary"] == "Real Gemini-shaped response."
