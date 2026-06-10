"""Sample LangGraph node functions for the ProjectVault report."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict


class DemoState(TypedDict):
    input_dir: str
    output_dir: str
    files: list[str]
    notes: list[str]
    warnings: list[str]


def build_demo_state(input_dir: Path, output_dir: Path) -> DemoState:
    return {
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "files": [],
        "notes": [],
        "warnings": [],
    }


def scan_files(state: DemoState) -> DemoState:
    input_dir = Path(state["input_dir"])
    files = [str(path) for path in input_dir.rglob("*") if path.is_file()] if input_dir.exists() else []
    return {**state, "files": files}


def plan_obsidian_notes(state: DemoState) -> DemoState:
    notes = [
        "00_Project_Index.md",
        "01_Assignment_Checklist.md",
        "05_Next_Actions.md",
    ]
    return {**state, "notes": notes}


def run_demo_workflow(state: DemoState) -> DemoState:
    state = scan_files(state)
    state = plan_obsidian_notes(state)
    return state
