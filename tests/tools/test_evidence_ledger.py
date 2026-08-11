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
    assert states["uploaded"] == "uploaded-remotely-verified"
    assert states["remotely-verified"] == "remote-readback-verified"
    assert states["released"] == "reconciled-release"
    assert states["captured"] == "original-and-datastore-fallback-captured"
    assert states["unavailable"] == "tombstoned"
    assert states["restricted"] == "rights-restricted"
    outcomes = document["treasury_resource_outcomes"]
    assert outcomes["original_source_captured"] == 12
    assert outcomes["datastore_fallback_captured"] == 44
    assert outcomes["authoritative_replacement_evidenced"] == 31
    assert outcomes["unavailable_tombstoned"] == 1
    assert outcomes["rights_restricted"] == 2
    assert outcomes["counts_are_mutually_exclusive"] is False
