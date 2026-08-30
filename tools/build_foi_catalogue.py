"""Build a local immutable source-catalogue candidate without capture or upload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.foi_catalogue import build_catalogue, catalogue_files, load_seeds


def main() -> int:
    """Write an index candidate, refusing to overwrite a different snapshot."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds", type=Path, default=Path(__file__).resolve().parents[1] / "config/foi"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    catalogue = build_catalogue(*load_seeds(args.seeds))
    files = catalogue_files(catalogue)
    for name, data in files.items():
        target = args.output / name
        if target.exists() and target.read_bytes() != data:
            parser.error(
                "output already contains a different snapshot; use a new directory"
            )
    args.output.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (args.output / name).write_bytes(data)
    print(json.dumps(catalogue["coverage"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
