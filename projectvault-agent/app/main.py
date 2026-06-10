"""CLI entry point for ProjectVault Agent."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from app.graph.build_graph import build_projectvault_graph
from app.graph.state import ProjectVaultState


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="projectvault-agent",
        description="Generate an Obsidian-ready project workspace from local course/project files.",
    )
    parser.add_argument("--input", required=True, type=Path, help="Input workspace directory.")
    parser.add_argument("--output", required=True, type=Path, help="Output Obsidian vault directory.")
    parser.add_argument(
        "--mode",
        choices=("dry-run", "write"),
        default="dry-run",
        help="Use dry-run to avoid Obsidian/graph writes and external API calls. Use write to create output files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = args.input.expanduser().resolve()
    output_path = args.output.expanduser().resolve()

    print("ProjectVault Agent initialized")
    print(f"Input path: {input_path}")
    print(f"Output path: {output_path}")
    print(f"Mode: {args.mode}")

    state: ProjectVaultState = {
        "input_dir": str(input_path),
        "output_dir": str(output_path),
        "mode": args.mode,
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
    graph = build_projectvault_graph()
    result = graph.invoke(state)

    print(f"Files discovered: {len(result['files'])}")
    if args.mode == "dry-run":
        type_counts = Counter(str(file_item.get("file_type", "document")) for file_item in result["files"])
        print("File type counts:")
        if type_counts:
            for file_type, count in sorted(type_counts.items()):
                print(f"  {file_type}: {count}")
        else:
            print("  none: 0")
    print(f"Analyzed files: {len(result['analyzed_files'])}")
    print(f"Graph nodes: {len(result['graph_nodes'])}")
    print(f"Graph edges: {len(result['graph_edges'])}")
    print(f"Obsidian files planned: {len(result['obsidian_files'])}")
    print(f"Sheets rows prepared: {len(result['sheets_rows'])}")
    if result.get("sheets_result"):
        print(f"Sheets status: {result['sheets_result'].get('status')}")
    if result["warnings"]:
        print(f"Warnings: {len(result['warnings'])}")


if __name__ == "__main__":
    main()
