"""Replay one explicitly pinned Silver selection without whole-source claims."""

# ruff: noqa: INP001 -- standalone evidence recipe.

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from archive_govt_nz.domains.health_appropriations.direct_coverage import Pinned
from archive_govt_nz.domains.health_appropriations.expanded_coverage import (
    selection_report,
)

REGISTER_SHA256 = "9b98964afb552761dc59815ea3912b49d95162c18abe43e396057f14f3e0875a"
CORE_RECEIPT_SHA256 = "23ddc3fb0a3d4d6dc55a4731694f7d9e26f5ace1324d4a76456f1ad761abe651"


def _pin(path: Path, digest: str) -> Pinned:
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != digest:
        message = "expanded_coverage_replay_fixity"
        raise ValueError(message)
    return Pinned(payload, digest)


def replay(archive: Path) -> dict[str, Any]:
    """Join the fixed selection register to its retained Silver manifest."""
    evidence = Path(__file__).resolve().parent
    register = _pin(evidence / "selections.json", REGISTER_SHA256)
    receipt = _pin(
        archive / "silver/raw-befu-core-expense-20260925-v1/MANIFEST.json",
        CORE_RECEIPT_SHA256,
    )
    report = selection_report(
        register,
        {"befu-core-expense-BEFU-2026": receipt},
        completion=None,
    )
    return {
        "schema_version": "archive-govt-nz.health-expanded-coverage-replay/v1",
        "register_sha256": REGISTER_SHA256,
        "selection_report": report,
        "qualification": "one-explicit-selection_metadata-join_only_no-phase-closure",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    print(json.dumps(replay(args.archive), sort_keys=True, indent=2))  # noqa: T201
