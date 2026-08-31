"""Extract a literal BEFU/HYEFU Health summary into a new Silver directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.domains.health_appropriations.forecast import (
    FORECAST_PROFILES,
    normalize_forecast_workbook,
)


def main() -> int:
    """Keep source profiles, observed context, output bytes and failures explicit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--profile", choices=FORECAST_PROFILES, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--source-vintage", required=True)
    parser.add_argument("--source-locator", required=True)
    args = parser.parse_args()
    result = normalize_forecast_workbook(
        args.source,
        args.output_dir,
        expected_sha256=args.expected_sha256,
        profile=args.profile,
        observed_at=args.observed_at,
        source_vintage=args.source_vintage,
        source_locator=args.source_locator,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
