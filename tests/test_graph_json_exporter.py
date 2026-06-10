from __future__ import annotations

import json
from pathlib import Path

from app.exporters.graph_json_exporter import GraphJsonExporter
from app.graph.state import ProjectVaultState
from app.knowledge.graph_builder import ProjectGraphBuilder


def _sample_state(tmp_path: Path, mode: str = "dry-run") -> ProjectVaultState:
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
        {
            "file_path": str(code),
            "file_type": "source_code",
            "summary": "Simple Python entrypoint.",
            "concepts": [{"name": "LangGraph", "description": "Duplicate concept should merge"}],
            "requirements": [],
            "tasks": [{"title": "실행 예시 추가", "priority": "HIGH", "reason": "중복 task should merge"}],
            "errors": [],
            "decisions": [],
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


def test_graph_builder_merges_duplicate_concepts_and_tasks(tmp_path: Path) -> None:
    state = _sample_state(tmp_path)

    concept_nodes = [node for node in state["graph_nodes"] if node["type"] == "Concept"]
    task_nodes = [node for node in state["graph_nodes"] if node["type"] == "Task"]
    relations = {edge["relation"] for edge in state["graph_edges"]}

    assert len([node for node in state["graph_nodes"] if node["type"] == "Project"]) == 1
    assert len([node for node in state["graph_nodes"] if node["type"] == "File"]) == 2
    assert len(concept_nodes) == 1
    assert len(task_nodes) == 1
    assert {"CONTAINS", "MENTIONS", "REQUIRES", "OCCURS_IN", "AFFECTS", "DEPENDS_ON", "SUPPORTS"} <= relations


def test_graph_json_exporter_uses_relation_field_and_writes_in_write_mode(tmp_path: Path) -> None:
    state = _sample_state(tmp_path, mode="write")

    planned_file = GraphJsonExporter().export(state)

    assert planned_file["path"] == "graph.json"
    payload = planned_file["payload"]
    assert payload["nodes"][0]["id"] == "project:local"
    assert payload["nodes"][0]["type_label"] == "프로젝트"
    assert "relation" in payload["edges"][0]
    assert "type" not in payload["edges"][0]
    assert (Path(state["output_dir"]) / "graph.json").exists()

    written = json.loads((Path(state["output_dir"]) / "graph.json").read_text(encoding="utf-8"))
    assert written == payload
