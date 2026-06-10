"""Google Sheets summary exporter."""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import Settings
from app.graph.state import ProjectVaultState
from app.knowledge.schema import EdgeType, NodeType

logger = logging.getLogger(__name__)

SHEETS_HEADER = [
    "timestamp",
    "project_name",
    "item_type",
    "title",
    "priority",
    "source_file",
    "reason",
    "related_links",
    "status",
]
SHEETS_ITEM_TYPES = {
    NodeType.REQUIREMENT.value,
    NodeType.TASK.value,
    NodeType.ERROR.value,
    NodeType.DECISION.value,
    NodeType.CONCEPT.value,
    NodeType.FILE.value,
}
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SheetsExporter:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()

    def build_rows(self, state: ProjectVaultState) -> list[list[str]]:
        return build_sheets_rows(state)

    def save(self, state: ProjectVaultState) -> dict[str, Any]:
        rows = build_sheets_rows(state)
        warnings: list[str] = []

        if state["mode"] == "dry-run":
            path = save_rows_to_local_json(rows, state["output_dir"])
            return {
                "status": "dry-run",
                "rows": rows,
                "saved_rows": 0,
                "local_path": path,
                "message": "dry-run: Google Sheets 저장 예정",
                "warnings": warnings,
            }

        if not self.settings.google_sheets_enabled:
            warning = "Google Sheets disabled; saved rows to local sheets_rows.json."
            warnings.append(warning)
            path = save_rows_to_local_json(rows, state["output_dir"])
            return {
                "status": "local-fallback",
                "rows": rows,
                "saved_rows": 0,
                "local_path": path,
                "message": warning,
                "warnings": warnings,
            }

        result = save_rows_to_google_sheets(rows)
        if result.get("success"):
            return {
                "status": "google-sheets",
                "rows": rows,
                "saved_rows": result.get("updated_rows", 0),
                "google_result": result,
                "message": f"Google Sheets append complete: {result.get('updated_rows', 0)} rows",
                "warnings": warnings,
            }

        warning = str(result.get("warning") or "Google Sheets append failed; saved rows to local sheets_rows.json.")
        warnings.append(warning)
        path = save_rows_to_local_json(rows, state["output_dir"])
        return {
            "status": "local-fallback",
            "rows": rows,
            "saved_rows": 0,
            "local_path": path,
            "google_result": result,
            "message": warning,
            "warnings": warnings,
        }


def build_sheets_rows(state: ProjectVaultState) -> list[list[str]]:
    timestamp = datetime.now(UTC).isoformat()
    project_name = Path(state["input_dir"]).name or "ProjectVault"
    nodes_by_id = {str(node.get("id", "")): node for node in state["graph_nodes"]}
    rows = [SHEETS_HEADER.copy()]

    for node in state["graph_nodes"]:
        item_type = str(node.get("type", ""))
        if item_type not in SHEETS_ITEM_TYPES:
            continue

        node_id = str(node.get("id", ""))
        properties = node.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}

        rows.append(
            [
                timestamp,
                project_name,
                item_type,
                str(node.get("label", "")),
                _priority(item_type, properties),
                _source_file(node_id, item_type, state["graph_edges"], nodes_by_id),
                _reason(item_type, properties),
                _related_links(node_id, state["graph_edges"], nodes_by_id),
                "TODO" if item_type in {NodeType.TASK.value, NodeType.REQUIREMENT.value, NodeType.ERROR.value} else "ACTIVE",
            ]
        )

    return rows


def save_rows_to_google_sheets(rows: list[list[str]]) -> dict[str, Any]:
    settings = Settings.from_env()
    credentials_path = settings.google_sheets_service_account_path

    if not settings.google_sheets_enabled:
        return {"success": False, "warning": "GOOGLE_SHEETS_ENABLED is not true."}
    if not settings.google_sheets_spreadsheet_id:
        return {"success": False, "warning": "GOOGLE_SHEETS_SPREADSHEET_ID is not set."}
    if credentials_path is None:
        return {"success": False, "warning": "Google Sheets service account credentials path is not set."}
    if not credentials_path.exists():
        return {"success": False, "warning": f"Google Sheets credentials file does not exist: {credentials_path}"}

    data_rows = rows[1:] if rows and rows[0] == SHEETS_HEADER else rows
    if not data_rows:
        return {"success": True, "updated_rows": 0, "response": {}}

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=SHEETS_SCOPES,
        )
        service = _build_sheets_service(credentials, settings.google_sheets_timeout_seconds)
        last_exc: Exception | None = None
        attempts = max(settings.google_sheets_retries, 0) + 1
        for attempt in range(1, attempts + 1):
            try:
                response = (
                    service.spreadsheets()
                    .values()
                    .append(
                        spreadsheetId=settings.google_sheets_spreadsheet_id,
                        range=settings.google_sheets_range,
                        valueInputOption="RAW",
                        insertDataOption="INSERT_ROWS",
                        body={"values": data_rows},
                    )
                    .execute()
                )
                updates = response.get("updates", {}) if isinstance(response, dict) else {}
                return {
                    "success": True,
                    "updated_rows": int(updates.get("updatedRows", len(data_rows))),
                    "response": response,
                    "attempts": attempt,
                }
            except Exception as exc:
                last_exc = exc
                logger.warning("Google Sheets append attempt %s/%s failed: %s", attempt, attempts, exc)
                if attempt < attempts:
                    time.sleep(min(2 * attempt, 5))
        return {
            "success": False,
            "warning": f"Google Sheets append failed after {attempts} attempt(s): {last_exc}",
        }
    except Exception as exc:
        logger.warning("Google Sheets append failed: %s", exc)
        return {"success": False, "warning": f"Google Sheets append failed: {exc}"}


def _build_sheets_service(credentials: Any, timeout_seconds: float) -> Any:
    try:
        import httplib2
        from google_auth_httplib2 import AuthorizedHttp
        from googleapiclient.discovery import build

        http = AuthorizedHttp(credentials, http=httplib2.Http(timeout=timeout_seconds))
        return build("sheets", "v4", http=http, cache_discovery=False)
    except Exception:
        from googleapiclient.discovery import build

        return build(
            "sheets",
            "v4",
            credentials=credentials,
            cache_discovery=False,
            client_options={"quota_project_id": None},
        )


def save_rows_to_local_json(rows: list[list[str]], output_dir: str) -> str:
    path = Path(output_dir) / "sheets_rows.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "columns": rows[0] if rows else [],
        "rows": rows[1:] if rows and rows[0] == SHEETS_HEADER else rows,
        "raw_rows": rows,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def _priority(item_type: str, properties: dict[str, Any]) -> str:
    if item_type == NodeType.TASK.value:
        return str(properties.get("priority", "MEDIUM"))
    if item_type in {NodeType.REQUIREMENT.value, NodeType.ERROR.value}:
        return "HIGH"
    return ""


def _reason(item_type: str, properties: dict[str, Any]) -> str:
    if item_type == NodeType.CONCEPT.value:
        return str(properties.get("description", ""))
    if item_type == NodeType.FILE.value:
        return str(properties.get("content_preview", ""))
    return str(properties.get("reason", "") or properties.get("source", ""))


def _source_file(
    node_id: str,
    item_type: str,
    edges: list[dict],
    nodes_by_id: dict[str, dict],
) -> str:
    if item_type == NodeType.FILE.value:
        return str(nodes_by_id.get(node_id, {}).get("label", ""))

    file_labels: list[str] = []
    for edge in edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        relation = str(edge.get("relation", edge.get("type", "")))
        if target == node_id and relation in {EdgeType.MENTIONS.value, EdgeType.REQUIRES.value, EdgeType.SUPPORTS.value}:
            source_node = nodes_by_id.get(source)
            if source_node and source_node.get("type") == NodeType.FILE.value:
                file_labels.append(str(source_node.get("label", "")))
        if source == node_id and relation in {EdgeType.OCCURS_IN.value, EdgeType.AFFECTS.value}:
            target_node = nodes_by_id.get(target)
            if target_node and target_node.get("type") == NodeType.FILE.value:
                file_labels.append(str(target_node.get("label", "")))
    return "; ".join(sorted(set(filter(None, file_labels))))


def _related_links(node_id: str, edges: list[dict], nodes_by_id: dict[str, dict]) -> str:
    related: list[str] = []
    for edge in edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source == node_id and target in nodes_by_id:
            related.append(_node_link(nodes_by_id[target]))
        elif target == node_id and source in nodes_by_id:
            related.append(_node_link(nodes_by_id[source]))
    return "; ".join(sorted(set(filter(None, related))))


def _node_link(node: dict[str, Any]) -> str:
    label = str(node.get("label", ""))
    node_id = str(node.get("id", ""))
    return f"{label} ({node_id})" if label else node_id
