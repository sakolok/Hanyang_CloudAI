from __future__ import annotations

import json
from pathlib import Path

from app.graph.build_graph import build_projectvault_graph
from app.graph.nodes import (
    analyze_files,
    build_project_graph,
    export_graph_json,
    generate_final_report,
    generate_obsidian_notes,
    prepare_sheets_rows,
    save_sheets_summary,
    scan_project_folder,
)
from app.graph.state import ProjectVaultState


def _state(input_dir: Path, output_dir: Path, mode: str = "dry-run") -> ProjectVaultState:
    return {
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "mode": mode,  # type: ignore[typeddict-item]
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


def test_workflow_nodes_update_expected_state_fields(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    (input_dir / "assignment").mkdir(parents=True)
    (input_dir / "assignment" / "notice.txt").write_text("Submit report.", encoding="utf-8")

    state = _state(input_dir, output_dir)
    for node in (
        scan_project_folder,
        analyze_files,
        build_project_graph,
        generate_obsidian_notes,
        export_graph_json,
        prepare_sheets_rows,
        save_sheets_summary,
        generate_final_report,
    ):
        state = node(state)

    assert len(state["files"]) == 1
    assert len(state["analyzed_files"]) == 1
    assert state["graph_nodes"][0]["type"] == "Project"
    assert state["obsidian_files"]
    assert state["sheets_rows"][0] == [
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
    assert "그래프 리포트" in state["final_report"]
    assert (output_dir / "sheets_rows.json").exists()


def test_build_projectvault_graph_runs_dry_run(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    (input_dir / "code").mkdir(parents=True)
    (input_dir / "code" / "main.py").write_text("print('hello')\n", encoding="utf-8")

    result = build_projectvault_graph().invoke(_state(input_dir, output_dir))

    assert len(result["files"]) == 1
    assert len(result["analyzed_files"]) == 1
    assert len(result["graph_nodes"]) >= 2
    file_rows = [row for row in result["sheets_rows"] if row[2] == "File"]
    assert any(row[3] == "code/main.py" for row in file_rows)
    assert (output_dir / "sheets_rows.json").exists()


def test_workflow_write_mode_creates_output_files(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    (input_dir / "README.md").write_text("Sample readme", encoding="utf-8")

    result = build_projectvault_graph().invoke(_state(input_dir, output_dir, mode="write"))

    assert result["obsidian_files"]
    assert (output_dir / "00_Project_Index.md").exists()
    assert (output_dir / "graph.json").exists()
    assert (output_dir / "sheets_rows.json").exists()
    assert (output_dir / "GRAPH_REPORT.md").exists()

    graph_payload = json.loads((output_dir / "graph.json").read_text(encoding="utf-8"))
    assert graph_payload["nodes"]
    assert graph_payload["edges"]
