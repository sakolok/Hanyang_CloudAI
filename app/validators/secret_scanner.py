"""Secret and credential risk scanner."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

RISKY_FILENAMES = {
    ".env",
    "credentials.json",
    "token.json",
    "service_account.json",
    "client_secret.json",
}

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("GEMINI_API_KEY", re.compile(r"\bGEMINI_API_KEY\s*=\s*[^\s#]+", re.IGNORECASE)),
    ("GOOGLE_API_KEY", re.compile(r"\bGOOGLE_API_KEY\s*=\s*[^\s#]+", re.IGNORECASE)),
    ("Google API key", re.compile(r"\bA[I]za[0-9A-Za-z_-]{20,}\b")),
    ("Private key", re.compile(r"-----BEGIN\s+PRIVATE\s+KEY-----")),
    ("password", re.compile(r"\bpassword\s*=\s*[^\s#]+", re.IGNORECASE)),
    ("secret", re.compile(r"\bsecret\s*=\s*[^\s#]+", re.IGNORECASE)),
    ("access_token", re.compile(r"\baccess_token\b\s*[:=]\s*['\"]?[^'\"\s,}]+['\"]?|\baccess_token\b", re.IGNORECASE)),
    ("refresh_token", re.compile(r"\brefresh_token\b\s*[:=]\s*['\"]?[^'\"\s,}]+['\"]?|\brefresh_token\b", re.IGNORECASE)),
)

TEXT_SUFFIXES = {".txt", ".md", ".py", ".json", ".env", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".log"}


def scan_secret_risks(input_dir: str) -> list[dict[str, Any]]:
    """Return secret-like findings without exposing secret values."""

    root = Path(input_dir).expanduser()
    if not root.exists():
        return []

    findings: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        relative_path = _relative_path(path, root)
        if path.name in RISKY_FILENAMES:
            findings.append(
                {
                    "risk_type": "risky_filename",
                    "file_path": str(path),
                    "relative_path": relative_path,
                    "filename": path.name,
                    "line_number": None,
                    "pattern": path.name,
                    "message": f"Risky credential filename detected: {path.name}",
                    "redacted_excerpt": "",
                }
            )

        if _should_scan_content(path):
            findings.extend(_scan_content(path, root))

    return findings


def build_security_analyses(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert scanner findings into Gemini-like analysis records."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for finding in findings:
        grouped[str(finding["file_path"])].append(finding)

    analyses: list[dict[str, Any]] = []
    for file_path, file_findings in grouped.items():
        filename = str(file_findings[0].get("filename", Path(file_path).name))
        errors = [_finding_to_error(finding) for finding in file_findings]
        tasks = _tasks_for_findings(file_findings)
        analyses.append(
            {
                "file_path": file_path,
                "file_type": "security_risk",
                "summary": f"Security scanner found {len(file_findings)} potential secret exposure risk(s) in {filename}.",
                "concepts": [
                    {
                        "name": "Secret Management",
                        "description": "Keep API keys and credentials out of submitted files and source control.",
                    }
                ],
                "requirements": [],
                "tasks": tasks,
                "errors": errors,
                "decisions": [],
                "source": "secret_scanner",
            }
        )
    return analyses


def redacted_line(line: str, pattern: re.Pattern[str] | None = None) -> str:
    """Mask a secret-like line while preserving enough context for remediation."""

    text = line.rstrip("\n\r")
    if pattern:
        text = pattern.sub("[REDACTED]", text)
    for _, compiled in SECRET_PATTERNS:
        text = compiled.sub("[REDACTED]", text)
    if len(text) > 180:
        text = f"{text[:177]}..."
    return text


def redact_text(text: str) -> str:
    """Redact all known secret-like patterns from text."""

    redacted = text
    for _, compiled in SECRET_PATTERNS:
        redacted = compiled.sub("[REDACTED]", redacted)
    return redacted


def _scan_content(path: Path, root: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return []
    except OSError:
        return []

    findings: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        for pattern_name, pattern in SECRET_PATTERNS:
            if not pattern.search(line):
                continue
            findings.append(
                {
                    "risk_type": "secret_pattern",
                    "file_path": str(path),
                    "relative_path": _relative_path(path, root),
                    "filename": path.name,
                    "line_number": line_number,
                    "pattern": pattern_name,
                    "message": f"Secret-like pattern detected: {pattern_name}",
                    "redacted_excerpt": redacted_line(line, pattern),
                }
            )
    return findings


def _finding_to_error(finding: dict[str, Any]) -> dict[str, Any]:
    line_number = finding.get("line_number")
    location = str(finding.get("relative_path", finding.get("filename", "")))
    if line_number:
        location = f"{location}:{line_number}"

    if finding.get("risk_type") == "risky_filename":
        title = f"위험 파일명 발견: {finding.get('filename')}"
    else:
        title = f"Secret-like pattern 발견: {finding.get('pattern')} ({location})"

    return {
        "title": title,
        "reason": f"{finding.get('message')} at {location}. Value is [REDACTED].",
        "source": "secret_scanner",
        "source_file": str(finding.get("relative_path", "")),
        "line_number": "" if line_number is None else str(line_number),
        "pattern": str(finding.get("pattern", "")),
        "redacted_excerpt": str(finding.get("redacted_excerpt", "")),
    }


def _tasks_for_findings(findings: list[dict[str, Any]]) -> list[dict[str, str]]:
    tasks_by_title: dict[str, dict[str, str]] = {}
    filenames = {str(finding.get("filename", "")) for finding in findings}
    has_secret_pattern = any(finding.get("risk_type") == "secret_pattern" for finding in findings)

    if ".env" in filenames:
        tasks_by_title[".env 파일 제출 제외 확인"] = {
            "title": ".env 파일 제출 제외 확인",
            "priority": "HIGH",
            "reason": ".env 파일은 API 키와 환경변수를 포함할 수 있으므로 제출물과 저장소에서 제외해야 합니다.",
            "source": "secret_scanner",
        }
    if filenames & {"credentials.json", "token.json", "service_account.json", "client_secret.json"}:
        tasks_by_title["credentials.json 제출 제외 확인"] = {
            "title": "credentials.json 제출 제외 확인",
            "priority": "HIGH",
            "reason": "Google 인증 JSON/token 파일은 제출물과 저장소에 포함되면 안 됩니다.",
            "source": "secret_scanner",
        }
    if has_secret_pattern:
        tasks_by_title["API 키 환경변수 처리 확인"] = {
            "title": "API 키 환경변수 처리 확인",
            "priority": "HIGH",
            "reason": "코드/문서에 secret-like 값이 감지되어 환경변수 또는 로컬 인증 파일로 분리해야 합니다.",
            "source": "secret_scanner",
        }

    return list(tasks_by_title.values())


def _should_scan_content(path: Path) -> bool:
    return path.name in RISKY_FILENAMES or path.suffix.lower() in TEXT_SUFFIXES or path.suffix == ""


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
