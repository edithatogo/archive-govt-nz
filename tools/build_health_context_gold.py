"""Build a verified context-only Gold coverage product from pinned Silver."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.domains.health_appropriations.context_gold import (
    export_context_gold,
)


def main() -> int:
    """Build the source-separated context observations and coverage mart."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--silver-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    receipt = export_context_gold(
        args.silver_root, args.source_root, args.output, write=args.write
    )
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
