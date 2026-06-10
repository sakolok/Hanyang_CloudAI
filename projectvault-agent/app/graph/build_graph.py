"""Build the ProjectVault LangGraph workflow."""

from __future__ import annotations

from typing import Callable, Protocol

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


class RunnableGraph(Protocol):
    def invoke(self, state: ProjectVaultState) -> ProjectVaultState:
        """Run the workflow and return the final state."""


WORKFLOW_STEPS: tuple[tuple[str, Callable[[ProjectVaultState], ProjectVaultState]], ...] = (
    ("scan_project_folder", scan_project_folder),
    ("analyze_files", analyze_files),
    ("build_project_graph", build_project_graph),
    ("generate_obsidian_notes", generate_obsidian_notes),
    ("export_graph_json", export_graph_json),
    ("prepare_sheets_rows", prepare_sheets_rows),
    ("save_sheets_summary", save_sheets_summary),
    ("generate_final_report", generate_final_report),
)


class SequentialProjectVaultGraph:
    """Fallback runner for environments where langgraph is not installed."""

    def invoke(self, state: ProjectVaultState) -> ProjectVaultState:
        for _, node in WORKFLOW_STEPS:
            state = node(state)
        return state


def build_projectvault_graph() -> RunnableGraph:
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        return SequentialProjectVaultGraph()

    workflow = StateGraph(ProjectVaultState)
    for name, node in WORKFLOW_STEPS:
        workflow.add_node(name, node)

    workflow.add_edge(START, "scan_project_folder")
    workflow.add_edge("scan_project_folder", "analyze_files")
    workflow.add_edge("analyze_files", "build_project_graph")
    workflow.add_edge("build_project_graph", "generate_obsidian_notes")
    workflow.add_edge("generate_obsidian_notes", "export_graph_json")
    workflow.add_edge("export_graph_json", "prepare_sheets_rows")
    workflow.add_edge("prepare_sheets_rows", "save_sheets_summary")
    workflow.add_edge("save_sheets_summary", "generate_final_report")
    workflow.add_edge("generate_final_report", END)

    return workflow.compile()
