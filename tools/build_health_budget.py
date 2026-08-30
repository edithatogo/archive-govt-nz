"""Extract raw Budget Health expenditure to a new local Silver directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.domains.health_appropriations.budget import (
    normalize_budget_workbook,
)


def main() -> int:
    """Verify source bytes and emit facts, lineage, dispositions and manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--source-vintage", required=True)
    parser.add_argument("--source-locator", required=True)
    args = parser.parse_args()
    result = normalize_budget_workbook(
        args.source,
        args.output_dir,
        expected_sha256=args.expected_sha256,
        observed_at=args.observed_at,
        source_vintage=args.source_vintage,
        source_locator=args.source_locator,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
