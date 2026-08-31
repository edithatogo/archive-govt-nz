"""Regression coverage for deterministic preservation evaluation receipts."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVALUATOR = ROOT / "tools" / "evaluate_preservation.py"


def _run_evaluator(receipt: Path) -> bytes:
    subprocess.run(
        [sys.executable, str(EVALUATOR), "--output", str(receipt)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return receipt.read_bytes()


def test_preservation_evaluation_is_deterministic_and_closed(tmp_path: Path) -> None:
    """Require closed integrity receipts and byte-stable reruns."""
    output = tmp_path / "preservation-packaging-evaluation.json"
    first = _run_evaluator(output)
    second = _run_evaluator(output)

    assert first == second

    receipt = json.loads(second)
    assert receipt["fixture_validation"]["valid"] is True
    assert receipt["ro_crate_validation"]["valid"] is True
    assert receipt["bagit_validation"]["valid"] is True
    assert receipt["ocfl_validation"]["valid"] is True
    assert receipt["conformance_claim"] == "bounded-structural-evaluation-only"
    assert receipt["decision"] == "bounded-profile-adoption"
    assert "RO-Crate" in receipt["decision_rationale"]
    assert {standard["name"] for standard in receipt["standards"]} == {
        "BagIt",
        "OCFL",
        "RO-Crate",
    }
