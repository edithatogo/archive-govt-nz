"""Prepare an eligibility-gated Ministry of Health package without publishing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

from archive_govt_nz.health_package import prepare_health_package


def main() -> int:
    """Build deterministic metadata, tombstone, derivative, and checksum artefacts."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--resources", type=Path, required=True)
    parser.add_argument("--classifications", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = prepare_health_package(args.resources, args.classifications, args.output)
    counts = cast("dict[str, object]", manifest["counts"])
    print(json.dumps({"output": str(args.output), **counts}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
