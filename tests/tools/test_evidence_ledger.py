"""Evidence ledger generation contracts."""

import json
import subprocess
from pathlib import Path


def test_evidence_ledger_preserves_stage_separation() -> None:
    """Publication states remain distinct from local validation evidence."""
    root = Path(__file__).parents[2]
    subprocess.run(
        ["uv", "run", "--locked", "python", "tools/generate_evidence_ledger.py"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    document = json.loads((root / "evidence/archive-evidence-ledger.json").read_text())
    states = {item["stage"]: item["state"] for item in document["stages"]}
    assert states["validated"] == "software-gates-passed"
    assert states["uploaded"] == "not-authorized"
    assert states["released"] == "not-released"
