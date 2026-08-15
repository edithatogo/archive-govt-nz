"""Classify discovered global CKAN resources into eligible captures and tombstones."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.global_policy import classify_global_manifest


def main() -> int:
    """Read global scope manifest and emit classification receipts."""
    parser = argparse.ArgumentParser(
        description="Classify global CKAN resources by licensing, scheme, and size."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("evidence/global-ckan-scope.json"),
        help="Input discovery manifest",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evidence/global-rights-classification.json"),
        help="Output classification receipt JSON",
    )
    args = parser.parse_args()

    manifest = json.loads(args.input.read_text(encoding="utf-8"))
    classification_receipt = classify_global_manifest(manifest)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(classification_receipt, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    counts = classification_receipt.get("counts", {})
    total = classification_receipt.get("total_resources_evaluated")
    print(f"Evaluated {total} resources: {json.dumps(counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
