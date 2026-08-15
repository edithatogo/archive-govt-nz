"""CLI tool to batch-materialize Parquet analytical derivatives from CAS objects."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.analytical_derivatives import (
    build_analytical_derivatives_suite,
)
from archive_govt_nz.object_store import ContentAddressedStore


def main() -> int:
    """Read capture receipt and generate Parquet derivatives for tabular objects."""
    parser = argparse.ArgumentParser(
        description="Materialize Parquet analytical derivatives from CAS."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("evidence/global-capture-receipt.json"),
        help="Input capture receipt JSON",
    )
    parser.add_argument(
        "--objects-dir",
        type=Path,
        default=Path("objects"),
        help="Root objects directory",
    )
    parser.add_argument(
        "--derivatives-dir",
        type=Path,
        default=Path("derivatives/parquet"),
        help="Output directory for Parquet derivatives",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evidence/analytical-derivatives-manifest.json"),
        help="Output manifest JSON path",
    )
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Capture receipt not found: {args.input}")
        return 1

    data = json.loads(args.input.read_text(encoding="utf-8"))
    captures = data.get("successful_captures", [])

    store = ContentAddressedStore(args.objects_dir)
    manifest = build_analytical_derivatives_suite(captures, store, args.derivatives_dir)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    mat = manifest.get("materialized_count", 0)
    tot = manifest.get("total_tabular_evaluated", 0)
    print(f"Analytical derivatives materialized: {mat}/{tot} -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
