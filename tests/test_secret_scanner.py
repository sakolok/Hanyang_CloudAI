from __future__ import annotations

from pathlib import Path

from app.graph.build_graph import build_projectvault_graph
from app.graph.state import ProjectVaultState
from app.validators.secret_scanner import build_security_analyses, redact_text, scan_secret_risks


def _state(input_dir: Path, output_dir: Path) -> ProjectVaultState:
    return {
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "mode": "dry-run",
        "files": [],
        "analyzed_files": [],
        "graph_nodes": [],
        "graph_edges": [],
        "obsidian_files": [],
        "sheets_rows": [],
        "sheets_result": {},
        "final_report": "",
        "warnings": [],
        "security_findings": [],
    }


def test_scan_secret_risks_detects_risky_filenames_and_patterns(tmp_path: Path) -> None:
    gemini_key_name = "GEMINI" + "_API_KEY"
    google_key_name = "GOOGLE" + "_API_KEY"
    gemini_secret = "gemini" + "-secret" + "-value"
    google_key = "AI" + "za" + "SyDUMMYDUMMYDUMMYDUMMYDUMMY"
    password_value = "plain" + "-text" + "-password"
    token_value = "token" + "-value"
    refresh_value = "refresh" + "-value"

    (tmp_path / ".env").write_text(f"{gemini_key_name}={gemini_secret}\n", encoding="utf-8")
    (tmp_path / "credentials.json").write_text('{"client_email": "svc@example.com"}', encoding="utf-8")
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "app.py").write_text(
        "\n".join(
            [
                f"{google_key_name}={google_key}",
                f"password={password_value}",
                f"access_token = '{token_value}'",
                f"refresh_token: {refresh_value}",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_secret_risks(str(tmp_path))

    patterns = {finding["pattern"] for finding in findings}
    assert ".env" in patterns
    assert "credentials.json" in patterns
    assert "GEMINI_API_KEY" in patterns
    assert "Google API key" in patterns
    assert "password" in patterns
    assert "access_token" in patterns
    assert "refresh_token" in patterns
    assert all(gemini_secret not in str(finding) for finding in findings)
    assert all(password_value not in str(finding) for finding in findings)
    assert all(token_value not in str(finding) for finding in findings)


def test_build_security_analyses_creates_errors_and_required_tasks(tmp_path: Path) -> None:
    google_key_name = "GOOGLE" + "_API_KEY"
    google_key = "AI" + "za" + "SyDUMMYDUMMYDUMMYDUMMYDUMMY"
    (tmp_path / ".env").write_text(f"{google_key_name}={google_key}\n", encoding="utf-8")
    (tmp_path / "service_account.json").write_text("{}", encoding="utf-8")

    analyses = build_security_analyses(scan_secret_risks(str(tmp_path)))
    tasks = [task["title"] for analysis in analyses for task in analysis["tasks"]]
    errors = [error for analysis in analyses for error in analysis["errors"]]

    assert ".env 파일 제출 제외 확인" in tasks
    assert "credentials.json 제출 제외 확인" in tasks
    assert "API 키 환경변수 처리 확인" in tasks
    assert errors
    assert all("[REDACTED]" in error["reason"] for error in errors)


def test_redact_text_masks_secret_values() -> None:
    gemini_key_name = "GEMINI" + "_API_KEY"
    token_value = "token" + "-value"
    text = f"{gemini_key_name}=abc123\naccess_token = '{token_value}'\nnormal text"

    redacted = redact_text(text)

    assert "abc123" not in redacted
    assert token_value not in redacted
    assert "[REDACTED]" in redacted


def test_secret_scan_integrates_with_workflow_without_leaking_values(tmp_path: Path) -> None:
    gemini_key_name = "GEMINI" + "_API_KEY"
    google_key_name = "GOOGLE" + "_API_KEY"
    env_secret = "very" + "-secret" + "-key"
    google_key = "AI" + "za" + "SyDUMMYDUMMYDUMMYDUMMYDUMMY"
    code_dir = tmp_path / "input" / "code"
    output_dir = tmp_path / "output"
    code_dir.mkdir(parents=True)
    (tmp_path / "input" / ".env").write_text(f"{gemini_key_name}={env_secret}\n", encoding="utf-8")
    (code_dir / "app.py").write_text(f"{google_key_name}={google_key}\n", encoding="utf-8")

    result = build_projectvault_graph().invoke(_state(tmp_path / "input", output_dir))

    error_nodes = [node for node in result["graph_nodes"] if node["type"] == "Error"]
    task_nodes = [node for node in result["graph_nodes"] if node["type"] == "Task"]
    all_output = "\n".join(str(file_item.get("content", "")) for file_item in result["obsidian_files"])
    sheets_output = "\n".join("|".join(row) for row in result["sheets_rows"])

    assert any(node["properties"].get("source") == "secret_scanner" for node in error_nodes)
    assert any(node["label"] == ".env 파일 제출 제외 확인" for node in task_nodes)
    assert any(node["label"] == "API 키 환경변수 처리 확인" for node in task_nodes)
    assert env_secret not in all_output
    assert env_secret not in sheets_output
    assert google_key not in all_output
    assert google_key not in sheets_output
    assert "보안 점검" in result["final_report"]
