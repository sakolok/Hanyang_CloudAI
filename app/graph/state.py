"""Shared LangGraph state for the ProjectVault workflow."""

from __future__ import annotations

from typing import Literal, TypedDict


RunMode = Literal["dry-run", "write"]


class ProjectVaultState(TypedDict):
    input_dir: str
    output_dir: str
    mode: RunMode
    files: list[dict]
    analyzed_files: list[dict]
    graph_nodes: list[dict]
    graph_edges: list[dict]
    obsidian_files: list[dict]
    sheets_rows: list[list[str]]
    sheets_result: dict
    final_report: str
    warnings: list[str]
    security_findings: list[dict]


AgentState = ProjectVaultState
