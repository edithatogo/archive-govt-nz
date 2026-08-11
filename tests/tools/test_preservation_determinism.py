"""Regression coverage for deterministic preservation evaluation receipts."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVALUATOR = ROOT / "tools" / "evaluate_preservation.py"
RECEIPT = ROOT / "evidence" / "preservation-packaging-evaluation.json"


def _run_evaluator() -> bytes:
    subprocess.run(
        [sys.executable, str(EVALUATOR)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return RECEIPT.read_bytes()


def test_preservation_evaluation_is_deterministic_and_closed() -> None:
    """Require closed integrity receipts and byte-stable reruns."""
    first = _run_evaluator()
    second = _run_evaluator()

    assert first == second

    receipt = json.loads(second)
    assert receipt["fixture_validation"]["valid"] is True
    assert receipt["ro_crate_validation"]["valid"] is True
    assert receipt["bagit_validation"]["valid"] is True
    assert receipt["ocfl_validation"]["valid"] is True
    assert receipt["conformance_claim"] == "bounded-structural-evaluation-only"
