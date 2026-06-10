"""LangGraph workflow node implementations."""

from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.exporters.graph_json_exporter import GraphJsonExporter
from app.exporters.obsidian_exporter import ObsidianExporter
from app.exporters.sheets_exporter import SheetsExporter, build_sheets_rows
from app.extractors.gemini_extractor import GeminiExtractor
from app.graph.state import ProjectVaultState
from app.ingestors.file_ingestor import scan_input_folder
from app.knowledge.graph_builder import ProjectGraphBuilder
from app.validators.secret_scanner import build_security_analyses, redact_text, scan_secret_risks


def scan_project_folder(state: ProjectVaultState) -> ProjectVaultState:
    print(f"Scanning input folder: {state['input_dir']}", flush=True)
    files = scan_input_folder(state["input_dir"])
    warnings = [warning for file_item in files for warning in file_item.get("warnings", [])]
    print(f"Scan complete: {len(files)} supported file(s) found", flush=True)
    return {**state, "files": files, "warnings": [*state.get("warnings", []), *warnings]}


def analyze_files(state: ProjectVaultState) -> ProjectVaultState:
    security_findings = scan_secret_risks(state["input_dir"])
    safe_files = [_redact_file_item(file_item) for file_item in state["files"]]
    extractor = GeminiExtractor(
        settings=Settings.from_env(),
        dry_run=state["mode"] == "dry-run",
    )
    if extractor.dry_run or not extractor.settings.gemini_api_key:
        print("Analyzing files with fake extractor", flush=True)
    else:
        print(
            f"Analyzing files with Gemini model {extractor.settings.gemini_model} "
            f"(timeout {extractor.settings.gemini_timeout_seconds:g}s per file)",
            flush=True,
        )

    analyzed_files = []
    total_files = len(safe_files)
    for index, file_item in enumerate(safe_files, start=1):
        filename = str(file_item.get("filename", file_item.get("path", "unknown")))
        print(f"Analyzing file {index}/{total_files}: {filename}", flush=True)
        analyzed_files.append(extractor.analyze_file(file_item))
    print(f"Analysis complete: {len(analyzed_files)} file analysis result(s)", flush=True)
    security_analyses = build_security_analyses(security_findings)
    warnings = state["warnings"]
    if security_findings:
        warnings = [*warnings, f"Security scanner found {len(security_findings)} potential secret exposure risk(s)."]
    return {
        **state,
        "files": safe_files,
        "analyzed_files": [*analyzed_files, *security_analyses],
        "security_findings": security_findings,
        "warnings": warnings,
    }


def build_project_graph(state: ProjectVaultState) -> ProjectVaultState:
    graph = ProjectGraphBuilder().build(
        files=state["files"],
        analyzed_files=state["analyzed_files"],
        input_dir=state["input_dir"],
    )
    return {**state, "graph_nodes": graph["nodes"], "graph_edges": graph["edges"]}


def generate_obsidian_notes(state: ProjectVaultState) -> ProjectVaultState:
    planned_files = ObsidianExporter().export(state)
    return {**state, "obsidian_files": planned_files}


def export_graph_json(state: ProjectVaultState) -> ProjectVaultState:
    graph_file = GraphJsonExporter().export(state)
    return {**state, "obsidian_files": [*state["obsidian_files"], graph_file]}


def prepare_sheets_rows(state: ProjectVaultState) -> ProjectVaultState:
    return {**state, "sheets_rows": build_sheets_rows(state)}


def save_sheets_summary(state: ProjectVaultState) -> ProjectVaultState:
    result = SheetsExporter().save(state)
    warnings = [*state["warnings"], *result.get("warnings", [])]
    obsidian_files = state["obsidian_files"]
    local_path = result.get("local_path")
    if local_path:
        try:
            relative_path = Path(str(local_path)).resolve().relative_to(Path(state["output_dir"]).resolve()).as_posix()
        except ValueError:
            relative_path = str(local_path)
        obsidian_files = [
            *obsidian_files,
            {"path": relative_path, "content": "", "kind": "json", "status": result.get("status", "")},
        ]
    return {
        **state,
        "sheets_rows": result["rows"],
        "sheets_result": result,
        "warnings": warnings,
        "obsidian_files": obsidian_files,
    }


def generate_final_report(state: ProjectVaultState) -> ProjectVaultState:
    report_file = ObsidianExporter().build_graph_report(state)
    report = str(report_file["content"])

    if state["mode"] == "write":
        output_dir = Path(state["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")

    obsidian_files = [
        file_item for file_item in state["obsidian_files"] if str(file_item.get("path", "")) != "GRAPH_REPORT.md"
    ]
    obsidian_files.append(report_file)
    return {**state, "final_report": report, "obsidian_files": obsidian_files}


def _append_analysis_nodes(nodes: list[dict], edges: list[dict], file_id: str, analysis: dict) -> None:
    specs = (
        ("concepts", "Concept", "mentions", "name"),
        ("requirements", "Requirement", "requires", "title"),
        ("tasks", "Task", "has_task", "title"),
        ("errors", "Error", "has_error", "title"),
        ("decisions", "Decision", "decides", "title"),
    )
    for field_name, node_type, edge_type, label_key in specs:
        for index, item in enumerate(_list_of_dicts(analysis.get(field_name, []))):
            label = str(item.get(label_key, "")).strip()
            if not label:
                continue
            node_id = f"{node_type.lower()}:{_slug(file_id)}:{index}:{_slug(label)}"
            nodes.append({"id": node_id, "type": node_type, "label": label, "properties": item})
            edges.append({"source": file_id, "target": node_id, "type": edge_type, "properties": {}})


def _project_overview_note(state: ProjectVaultState) -> dict:
    content = "\n".join(
        [
            "# Project Overview",
            "",
            f"- Input: `{state['input_dir']}`",
            f"- Files scanned: {len(state['files'])}",
            f"- Graph nodes: {len(state['graph_nodes'])}",
            "",
        ]
    )
    return {"path": "notes/Project Overview.md", "content": content}


def _analysis_note(analysis: dict) -> dict:
    file_path = str(analysis.get("file_path", "unknown"))
    title = Path(file_path).name or "unknown"
    content = "\n".join(
        [
            f"# {title}",
            "",
            f"- File type: `{analysis.get('file_type', 'document')}`",
            "",
            "## Summary",
            "",
            str(analysis.get("summary", "")),
            "",
            "## Tasks",
            "",
            *_markdown_items(analysis.get("tasks", [])),
            "",
            "## Requirements",
            "",
            *_markdown_items(analysis.get("requirements", [])),
            "",
            "## Errors",
            "",
            *_markdown_items(analysis.get("errors", [])),
            "",
            "## Decisions",
            "",
            *_markdown_items(analysis.get("decisions", [])),
            "",
        ]
    )
    return {"path": f"notes/files/{_safe_filename(title)}.md", "content": content}


def _context_pack_note(state: ProjectVaultState) -> dict:
    lines = [
        "# Codex Context Pack",
        "",
        f"- Input workspace: `{state['input_dir']}`",
        f"- Files scanned: {len(state['files'])}",
        "",
        "## Files",
        "",
    ]
    lines.extend(f"- `{_relative_path(file_item, state['input_dir'])}`" for file_item in state["files"])
    lines.append("")
    return {"path": "CODEX_CONTEXT_PACK.md", "content": "\n".join(lines)}


def _markdown_items(items: object) -> list[str]:
    normalized = _list_of_dicts(items)
    if not normalized:
        return ["- None"]
    return [f"- {item.get('title') or item.get('name')} {f'({item.get('priority')})' if item.get('priority') else ''}".rstrip() for item in normalized]


def _join_titles(items: object) -> str:
    titles = []
    for item in _list_of_dicts(items):
        title = item.get("title") or item.get("name")
        if title:
            titles.append(str(title))
    return "; ".join(titles)


def _list_of_dicts(items: object) -> list[dict]:
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _relative_path(file_item: dict, input_dir: str) -> str:
    path = Path(str(file_item.get("path", "")))
    if not path:
        return "unknown"
    try:
        return path.resolve().relative_to(Path(input_dir).resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _safe_filename(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value).strip("_") or "note"


def _slug(value: str) -> str:
    return _safe_filename(value.lower())[:80]


def _redact_file_item(file_item: dict) -> dict:
    safe_item = dict(file_item)
    for key in ("content", "content_preview"):
        value = safe_item.get(key)
        if isinstance(value, str):
            safe_item[key] = redact_text(value)
    return safe_item
