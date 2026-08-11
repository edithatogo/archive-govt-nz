"""Preservation evaluation receipt contracts."""

import json
import subprocess
from pathlib import Path


def test_preservation_evaluation_is_bounded_and_non_adopting() -> None:
    """The evaluation records candidates without silently making them gates."""
    root = Path(__file__).parents[2]
    result = subprocess.run(
        ["uv", "run", "--locked", "python", "tools/evaluate_preservation.py"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "preservation-packaging-evaluation.json" in result.stdout
    document = json.loads(
        (root / "evidence/preservation-packaging-evaluation.json").read_text()
    )
    assert document["release_requirement"] is False
    assert document["decision"] == "bounded-profile-adoption"
    standards = {item["name"]: item for item in document["standards"]}
    assert set(standards) == {
        "OCFL",
        "RO-Crate",
        "BagIt",
    }
    assert standards["RO-Crate"]["status"] == "adopted-profile"
    assert standards["BagIt"]["status"] == "adopted-at-release"
    assert standards["OCFL"]["status"] == "deferred"
    assert document["ro_crate_validation"]["valid"] is True
