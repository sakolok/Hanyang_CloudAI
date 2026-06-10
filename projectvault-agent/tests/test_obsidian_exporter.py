from __future__ import annotations

from pathlib import Path

from app.exporters.obsidian_exporter import ObsidianExporter
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
            "tasks": [{"title": "API 키/보안: 점검", "priority": "HIGH", "reason": "과제 제출 전 보안 확인"}],
            "errors": [{"title": "API 키 노출 위험", "reason": ".env 제출 위험"}],
            "decisions": [{"title": "dry-run 우선 구현", "reason": "API 키 없이 시연"}],
        }
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


def test_obsidian_exporter_plans_required_notes_without_writing(tmp_path: Path) -> None:
    state = _sample_state(tmp_path)

    planned_files = ObsidianExporter().export(state)
    planned_by_path = {file_item["path"]: file_item for file_item in planned_files}

    assert "00_Project_Index.md" in planned_by_path
    assert "01_Assignment_Checklist.md" in planned_by_path
    assert "02_Lecture_Concepts.md" in planned_by_path
    assert "03_Code_Summary.md" in planned_by_path
    assert "04_Error_Log.md" in planned_by_path
    assert "05_Next_Actions.md" in planned_by_path
    assert "06_Codex_Context_Pack.md" in planned_by_path
    assert "GRAPH_REPORT.md" in planned_by_path
    assert "Concepts/LangGraph.md" in planned_by_path
    assert "Tasks/API_키_보안_점검.md" in planned_by_path
    assert not Path(state["output_dir"]).exists()

    index_content = str(planned_by_path["00_Project_Index.md"]["content"])
    task_content = str(planned_by_path["Tasks/API_키_보안_점검.md"]["content"])
    file_note = next(file_item for file_item in planned_files if str(file_item["path"]).startswith("Files/assignment_notice"))

    assert index_content.startswith("---")
    assert "[[01_Assignment_Checklist|과제 체크리스트]]" in index_content
    assert "## 해야 할 일" in task_content
    assert "## 왜 필요한가" in task_content
    assert "## 관련 파일" in task_content
    assert "## 관련 개념" in task_content
    assert "## 우선순위" in task_content
    assert "[[Concepts/LangGraph|LangGraph]]" in str(file_note["content"])


def test_obsidian_exporter_writes_files_with_safe_names(tmp_path: Path) -> None:
    state = _sample_state(tmp_path, mode="write")

    ObsidianExporter().export(state)

    output_dir = Path(state["output_dir"])
    assert (output_dir / "00_Project_Index.md").exists()
    assert (output_dir / "Tasks" / "API_키_보안_점검.md").exists()
    assert (output_dir / "Concepts" / "LangGraph.md").exists()
