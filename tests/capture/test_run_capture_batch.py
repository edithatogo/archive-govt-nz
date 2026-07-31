"""Bounded capture-runner contracts."""

import json
import subprocess
from pathlib import Path


def test_capture_runner_defaults_to_no_transfer(tmp_path: Path) -> None:
    """Without explicit enablement no source is contacted or stored."""
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"outcomes": []}), encoding="utf-8")
    output = tmp_path / "run.json"
    result = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/run_capture_batch.py",
            "--plan",
            str(plan),
            "--output",
            str(output),
            "--object-root",
            str(tmp_path / "objects"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "not-enabled" in result.stdout
    assert not output.exists()
