"""Build a local immutable source-catalogue candidate without capture or upload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.foi_canonical import build_source_index
from archive_govt_nz.foi_catalogue import catalogue_files
from archive_govt_nz.foi_discovery import build_reviewed_catalogue


def main() -> int:
    """Write an index candidate, refusing to overwrite a different snapshot."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds", type=Path, default=Path(__file__).resolve().parents[1] / "config/foi"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--canonical-track",
        type=Path,
        help="Opt in to the pinned canonical metadata index from this FOI track",
    )
    args = parser.parse_args()
    try:
        files = (
            build_source_index(args.seeds, args.canonical_track)
            if args.canonical_track is not None
            else catalogue_files(build_reviewed_catalogue(args.seeds))
        )
        _write_files(args.output, files)
    except OSError, ValueError, KeyError, TypeError:
        parser.error("invalid inputs or conflicting output; use a new directory")
    print(json.dumps(json.loads(files["coverage.json"]), indent=2))
    return 0


def _write_files(output: Path, files: dict[str, bytes]) -> None:
    """Preflight all paths; never follow links or truncate an existing file."""
    for path in (output, *output.parents):
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            msg = "output directory conflict"
            raise ValueError(msg)
    for name, data in files.items():
        target = output / name
        if target.is_symlink() or (
            target.exists() and (not target.is_file() or target.read_bytes() != data)
        ):
            msg = "output snapshot conflict"
            raise ValueError(msg)
    output.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        target = output / name
        if not target.exists():
            with target.open("xb") as stream:
                stream.write(data)


if __name__ == "__main__":
    raise SystemExit(main())
