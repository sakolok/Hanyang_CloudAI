"""Export a Codex Context Pack Markdown file."""

from __future__ import annotations

from pathlib import Path

from app.graph.state import AgentState


class ContextPackExporter:
    def export(self, state: AgentState) -> list[Path]:
        path = state.output_path / "CODEX_CONTEXT_PACK.md"
        lines = [
            "# Codex Context Pack",
            "",
            "## ProjectVault Agent Output",
            "",
            f"- Input workspace: `{state.input_path}`",
            f"- Output vault: `{state.output_path}`",
            f"- Files discovered: {len(state.files)}",
            "",
            "## File Index",
            "",
        ]
        lines.extend(f"- `{file_item.relative_path.as_posix()}`" for file_item in state.files)
        lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        return [path]

