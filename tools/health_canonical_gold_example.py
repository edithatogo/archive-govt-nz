"""Print a compact, read-only summary of an exact pinned canonical Gold package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from archive_govt_nz.domains.health_appropriations.canonical_gold_example import (
    summarize_verified_canonical_gold,
)


def main() -> int:
    """Parse arguments and emit the pinned package summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="verified Gold package directory")
    parser.add_argument("manifest_sha256", help="expected MANIFEST.json SHA-256")
    arguments = parser.parse_args()
    try:
        result = summarize_verified_canonical_gold(
            arguments.package, arguments.manifest_sha256
        )
    except ValueError:
        print("canonical_gold_example_invalid", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
