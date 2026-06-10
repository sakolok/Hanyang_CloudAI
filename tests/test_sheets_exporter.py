from __future__ import annotations

import json
from pathlib import Path

from app.config import Settings
from app.exporters import sheets_exporter
from app.exporters.sheets_exporter import (
    SHEETS_HEADER,
    SheetsExporter,
    build_sheets_rows,
    save_rows_to_google_sheets,
    save_rows_to_local_json,
)
from app.graph.state import ProjectVaultState
from app.knowledge.graph_builder import ProjectGraphBuilder


def _settings(enabled: bool = False) -> Settings:
    return Settings(
        gemini_api_key=None,
        gemini_model="gemini-test",
        gemini_timeout_seconds=30.0,
        google_sheets_enabled=enabled,
        google_sheets_spreadsheet_id="sheet-id" if enabled else None,
        google_sheets_range="ProjectVault!A:I",
        google_sheets_timeout_seconds=60.0,
        google_sheets_retries=2,
        google_application_credentials_path=None,
        google_sheets_credentials_file=None,
        google_sheets_credentials_path=None,
        google_sheets_token_path=None,
        google_service_account_path=None,
    )


def _state(tmp_path: Path, mode: str = "dry-run") -> ProjectVaultState:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    assignment = input_dir / "assignment" / "notice.txt"
    code = input_dir / "code" / "main.py"
    assignment.parent.mkdir(parents=True)
    code.parent.mkdir(parents=True)
    assignment.write_text("Submit execution example.", encoding="utf-8")
    code.write_text("print('hello')", encoding="utf-8")

    files = [
        {
            "path": str(assignment),
            "filename": "notice.txt",
            "extension": ".txt",
            "file_type": "assignment_notice",
            "content": "Submit execution example.",
            "content_preview": "Submit execution example.",
            "warnings": [],
        },
        {
            "path": str(code),
            "filename": "main.py",
            "extension": ".py",
            "file_type": "source_code",
            "content": "print('hello')",
            "content_preview": "print('hello')",
            "warnings": [],
        },
    ]
    analyzed_files = [
        {
            "file_path": str(assignment),
            "file_type": "assignment_notice",
            "summary": "Assignment requires execution examples.",
            "concepts": [{"name": "LangGraph", "description": "StateGraph workflow framework"}],
            "requirements": [{"title": "실행 예시 포함", "source": "notice.txt"}],
            "tasks": [{"title": "실행 예시 추가", "priority": "HIGH", "reason": "과제 요구사항"}],
            "errors": [{"title": "API 키 노출 위험", "reason": ".env 제출 위험"}],
            "decisions": [{"title": "dry-run 우선 구현", "reason": "API 키 없이 시연"}],
        },
    ]
    graph = ProjectGraphBuilder().build(files=files, analyzed_files=analyzed_files, input_dir=str(input_dir))
    return {
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "mode": mode,  # type: ignore[typeddict-item]
        "files": files,
        "analyzed_files": analyzed_files,
        "graph_nodes": graph["nodes"],
        "graph_edges": graph["edges"],
        "obsidian_files": [],
        "sheets_rows": [],
        "sheets_result": {},
        "final_report": "",
        "warnings": [],
        "security_findings": [],
    }


def test_build_sheets_rows_uses_required_columns_and_item_types(tmp_path: Path) -> None:
    rows = build_sheets_rows(_state(tmp_path))

    assert rows[0] == SHEETS_HEADER
    item_types = {row[2] for row in rows[1:]}
    assert {"Requirement", "Task", "Error", "Decision", "Concept", "File"} <= item_types
    task_row = next(row for row in rows if row[2] == "Task")
    assert task_row[4] == "HIGH"
    assert "assignment/notice.txt" in task_row[5]
    assert "실행 예시 포함" in task_row[7]


def test_save_rows_to_local_json_writes_rows(tmp_path: Path) -> None:
    rows = [SHEETS_HEADER, ["t", "project", "Task", "title", "HIGH", "file", "reason", "links", "TODO"]]

    path = save_rows_to_local_json(rows, str(tmp_path))

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["columns"] == SHEETS_HEADER
    assert payload["rows"][0][2] == "Task"
    assert payload["raw_rows"] == rows


def test_sheets_exporter_dry_run_writes_local_json(tmp_path: Path) -> None:
    state = _state(tmp_path, mode="dry-run")

    result = SheetsExporter(settings=_settings(enabled=False)).save(state)

    assert result["status"] == "dry-run"
    assert result["message"] == "dry-run: Google Sheets 저장 예정"
    assert Path(result["local_path"]).exists()


def test_sheets_exporter_write_without_credentials_falls_back(tmp_path: Path) -> None:
    state = _state(tmp_path, mode="write")

    result = SheetsExporter(settings=_settings(enabled=False)).save(state)

    assert result["status"] == "local-fallback"
    assert result["warnings"]
    assert Path(result["local_path"]).exists()


def test_sheets_exporter_write_with_enabled_settings_calls_google(monkeypatch, tmp_path: Path) -> None:
    state = _state(tmp_path, mode="write")
    called = {"value": False}

    def fake_save(rows: list[list[str]]) -> dict:
        called["value"] = True
        return {"success": True, "updated_rows": len(rows) - 1}

    monkeypatch.setattr(sheets_exporter, "save_rows_to_google_sheets", fake_save)

    result = SheetsExporter(settings=_settings(enabled=True)).save(state)

    assert called["value"] is True
    assert result["status"] == "google-sheets"
    assert result["saved_rows"] == len(result["rows"]) - 1


def test_save_rows_to_google_sheets_missing_credentials_warns(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_SHEETS_ENABLED", "true")
    monkeypatch.setenv("GOOGLE_SHEETS_SPREADSHEET_ID", "sheet-id")
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GOOGLE_SHEETS_CREDENTIALS_FILE", raising=False)
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_PATH", raising=False)
    monkeypatch.delenv("GOOGLE_SHEETS_CREDENTIALS_PATH", raising=False)

    result = save_rows_to_google_sheets([SHEETS_HEADER])

    assert result["success"] is False
    assert "credentials path is not set" in result["warning"]
