# /// script
# requires-python = ">=3.15.1"
# dependencies = ["polars>=1.35,<2"]
# ///
"""Reproducible optional Polars lazy projection of a verified election release.

Invocation: uv run --script tools/election_polars_export.py --source
    spaces/nz-election-explorer/data/2026-preliminary.json --output build/elections
The inline PEP 723 environment does not change the repository's locked core.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import polars as pl  # noqa: E402 -- sys.path configured for standalone script

from archive_govt_nz.domains.elections.polars_release import calculate_party_shares  # noqa: E402 -- standalone script


def main() -> None:
    """Write source-reconciled Parquet, CSV and a receipt."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "spaces/nz-election-explorer/data/2026-preliminary.json",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "build/elections")
    args = parser.parse_args()
    rows = calculate_party_shares(args.source)
    args.output.mkdir(parents=True, exist_ok=True)
    lazy = pl.DataFrame(rows).lazy()
    lazy.sink_parquet(args.output / "party-shares-2026-preliminary.parquet")
    lazy.collect().write_csv(args.output / "party-shares-2026-preliminary.csv")
    receipt = {
        "status": "source_reconciled",
        "election_year": 2026,
        "vintage": "preliminary",
        "party_count": len(rows),
        "total_votes": sum(row["votes"] for row in rows),
        "total_seats": sum(row["total_seats"] for row in rows),
        "engine": "polars",
        "polars_version": pl.__version__,
    }
    (args.output / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
