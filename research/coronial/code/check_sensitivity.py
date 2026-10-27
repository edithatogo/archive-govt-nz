"""Check all jurisdiction count/share comparisons from retained public aggregates."""

import csv
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
rows = list(csv.DictReader((root / "data/australian-coronial-observations.csv").open()))
expected = list(
    csv.DictReader((root / "results/within-jurisdiction-sensitivity.csv").open())
)
require(len(rows) == 1280, "Mismatch: len(rows) == 1280")
require(
    sum(bool(r["missing_code"]) for r in rows) == 97, "Expected 97 missing-code cells"
)


def value(region: str, period: str, metric: str) -> float:
    """Read one unambiguous count from the retained official table extraction."""
    matches = [
        r
        for r in rows
        if r["jurisdiction"] == region
        and r["period"] == period
        and r["metric"] == metric
        and r["table"] == "7A.21"
        and r["unit"] == "no."
    ]
    require(
        len(matches) == 1 and (not matches[0]["missing_code"]),
        "Expected one non-missing matching cell",
    )
    return float(matches[0]["value"])


calculated = []
for region in ["ACT", "NSW", "NT", "Qld", "SA", "Tas", "Vic", "WA"]:
    a, b = [value(region, p, "Pending case load") for p in ["2023-24", "2024-25"]]
    c, d = [value(region, p, "Cases >24 months") for p in ["2023-24", "2024-25"]]
    calc = {
        "jurisdiction": region,
        "pending_2023_24": a,
        "pending_2024_25": b,
        "pending_pct_change": round(100 * (b / a - 1), 2),
        "over24_count_2023_24": c,
        "over24_count_2024_25": d,
        "over24_count_pct_change": round(100 * (d / c - 1), 2),
        "over24_share_2023_24_derived": round(100 * c / a, 2),
        "over24_share_2024_25_derived": round(100 * d / b, 2),
    }
    retained = next(x for x in expected if x["jurisdiction"] == region)
    for key, item in calc.items():
        require(
            item == (retained[key] if key == "jurisdiction" else float(retained[key])),
            str((region, key)),
        )
    calculated.append(calc)
require(len(expected) == len(calculated) == 8, "Expected all eight jurisdictions")
print(
    json.dumps(
        {
            "status": "passed",
            "python": sys.version,
            "raw_rows": len(rows),
            "missing_cells_retained": 97,
            "jurisdictions_checked": len(calculated),
            "comparisons": calculated,
        },
        indent=2,
    )
)
