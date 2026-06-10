from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_dry_run_cli_initializes(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.main",
            "--input",
            str(input_dir),
            "--output",
            str(output_dir),
            "--mode",
            "dry-run",
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "ProjectVault Agent initialized" in result.stdout
    assert f"Input path: {input_dir.resolve()}" in result.stdout
    assert f"Output path: {output_dir.resolve()}" in result.stdout
    assert "Files discovered: 0" in result.stdout
