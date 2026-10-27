"""Reproduce the primary longitudinal display without changing retained results."""

import csv
import hashlib
import json
import sys
from pathlib import Path

# Frozen numerical checks deliberately use literal expected values; this is a
# standalone CLI recipe, not an importable application module.
# ruff: noqa: INP001, PLR2004, T201


def require(condition: bool, message: str) -> None:  # noqa: FBT001
    """Fail explicitly, including when Python optimization is enabled."""
    if not condition:
        raise SystemExit(message)


if sys.version_info[:3] != (3, 15, 1):
    message = "Use the qualified repository Python 3.15.1 interpreter"
    raise SystemExit(message)
root = Path(sys.argv[1]).resolve()
expected = json.loads((root / "results/descriptive-analysis.json").read_text())
raw = list(csv.DictReader((root / "data/annual-edition-observations.csv").open()))
unique = {}
for row in raw:
    key = (row["source_edition"], row["period"], row["metric"])
    if key in unique:
        require(unique[key]["value"] == row["value"], str(key))
    # Duplicate values are identical; retain the last captured locator/notes,
    # matching the independently checked canonical extraction.
    unique[key] = row
order = expected["edition_order"]
latest = {}
for row in unique.values():
    key = (row["period"], row["metric"])
    if key not in latest or order.index(row["source_edition"]) > order.index(
        latest[key]["source_edition"]
    ):
        latest[key] = row
retained = list(csv.DictReader((root / "results/primary-longitudinal.csv").open()))
require(
    [latest[k] for k in sorted(latest)] == retained,
    "Mismatch: [latest[k] for k in sorted(latest)] == retained",
)
recent = [
    r
    for r in unique.values()
    if r["metric"] == "mean_days_case_closure" and r["period"] >= "2020/21"
]
means = [
    latest[(y, "mean_days_case_closure")]["value"]
    for y in ("2020/21", "2021/22", "2022/23", "2023/24", "2024/25")
]
require(
    means == expected["recent_primary_means"],
    "Mismatch: means == expected['recent_primary_means']",
)
require(
    all(float(r["value"]) > 365 for r in recent),
    "Mismatch: all((float(r['value']) > 365 for r in recent))",
)
require(
    len(raw) == 100
    and len(unique) == 95
    and (len(latest) == 55)
    and (len(recent) == 8),
    "Expected 100 raw, 95 unique, 55 latest, and 8 recent cells",
)
groups = {}
for row in unique.values():
    groups.setdefault((row["period"], row["metric"]), []).append(row["value"])
repeated = [v for v in groups.values() if len(v) > 1]
changed = [v for v in repeated if len(set(v)) > 1]
require(
    len(repeated) == 40 and len(changed) == 29,
    "Mismatch: len(repeated) == 40 and len(changed) == 29",
)
print(
    json.dumps(
        {
            "status": "passed",
            "python": sys.version,
            "raw_rows": len(raw),
            "distinct_edition_cells": len(unique),
            "primary_cells": len(latest),
            "repeated_combinations": len(repeated),
            "changed_combinations": len(changed),
            "recent_primary_means": means,
            "all_retained_recent_means_exceed365": True,
            "primary_csv_sha256": hashlib.sha256(
                (root / "results/primary-longitudinal.csv").read_bytes()
            ).hexdigest(),
        },
        indent=2,
    )
)
