"""ProjectVault sample CLI.

This file is sample input for ProjectVault Agent. It does not call real APIs.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from graph_nodes import build_demo_state, run_demo_workflow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the ProjectVault sample workflow.")
    parser.add_argument("--input", default="./input_workspace", help="Input workspace directory.")
    parser.add_argument("--output", default="./output_vault", help="Output vault directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    state = build_demo_state(Path(args.input), Path(args.output))
    result = run_demo_workflow(state)
    print("Sample ProjectVault workflow completed")
    print(f"Input files: {len(result['files'])}")
    print(f"Planned notes: {len(result['notes'])}")


if __name__ == "__main__":
    main()
