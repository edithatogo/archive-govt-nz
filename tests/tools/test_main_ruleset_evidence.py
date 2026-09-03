"""Regression coverage for minimized hosted-ruleset evidence."""

from __future__ import annotations

import json
import runpy
import shutil
import subprocess
from pathlib import Path
from typing import cast

ROOT = Path(__file__).parents[2]
EVIDENCE = ROOT / "evidence" / "assurance" / "main-ruleset-20260903"
RECEIPT_EXCLUSION_PATTERN = cast(
    "str",
    runpy.run_path(str(ROOT / "tools" / "supply_chain.py"))[
        "RECEIPT_EXCLUSION_PATTERN"
    ],
)


def test_ruleset_evidence_is_minimized_and_has_no_secret_candidates() -> None:
    """Keep opaque fields out and run the production scanner over each JSON file."""
    projections = [
        EVIDENCE / "repository-rulesets-readback.json",
        EVIDENCE / "ruleset-22180861-readback.json",
    ]
    paths = [EVIDENCE / "main-ruleset-readback-receipt.json", *projections]
    for path in projections:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert '"node_id"' not in path.read_text(encoding="utf-8")
        assert '"_links"' not in path.read_text(encoding="utf-8")
        assert payload

    executable = shutil.which("detect-secrets")
    assert executable is not None
    result = subprocess.run(
        [
            executable,
            "scan",
            "--force-use-all-plugins",
            "--exclude-lines",
            RECEIPT_EXCLUSION_PATTERN,
            *map(str, paths),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout)["results"] == {}
