"""Print deterministic receipts from pinned retained Budget packages; read-only."""

# Standalone evidence recipe, not an importable package.
# ruff: noqa: INP001

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from archive_govt_nz.domains.health_appropriations.layout_drift import (
    compare_budget_layout,
)

PACKAGES = (
    (
        "budget-2025/v1",
        "raw-orchestrated-20260830-v1/budget",
        "1b1e5dfd3fa90d98dcf5200997001db236df7b40f4404b658c36f5cb0264d2fe",
    ),
    (
        "budget-2026/v1",
        "raw-budget-2026-20260831-v1",
        "f34000992fd65dca445e7ad251cb06df3c68107410355ea057ea9a2bf8481738",
    ),
)


def replay(silver_root: Path) -> dict:
    """Verify each retained package twice and preserve before/after byte hashes."""
    results = []
    for profile, name, pin in PACKAGES:
        package = silver_root / name
        members = (
            "MANIFEST.json",
            "budget_facts.parquet",
            "field_lineage.parquet",
            "row_dispositions.parquet",
        )
        before = {}
        for member in members:
            with (package / member).open("rb") as stream:
                before[member] = hashlib.file_digest(stream, "sha256").hexdigest()
        first = compare_budget_layout(package, pin, package, pin, profile=profile)
        second = compare_budget_layout(package, pin, package, pin, profile=profile)
        if first != second:
            message = "replay_nondeterministic"
            raise ValueError(message)
        for member, digest in before.items():
            with (package / member).open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                    message = "replay_input_changed"
                    raise ValueError(message)
        results.append(
            {
                "package": name,
                "input_sha256": before,
                "repeat_identical": True,
                "inputs_unchanged": True,
                "receipt": first,
            }
        )
    return {
        "schema_version": "archive-govt-nz.health-layout-replay/v1",
        "kind": "local_read_only_retained_package_replay",
        "self_comparisons_only": True,
        "cross_vintage_comparison": "not_permitted",
        "new_normalization": False,
        "original_reinspection": "not_performed",
        "results": results,
    }


if __name__ == "__main__":
    print(json.dumps(replay(Path(sys.argv[1])), sort_keys=True, indent=2))  # noqa: T201
