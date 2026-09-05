"""Validate the current FOI catalogue and emit honest phase accounting."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.foi_discovery import build_reviewed_catalogue
from archive_govt_nz.foi_phase_validation import validate_catalogue_phase


def main() -> int:
    """Render current structural and phase-acceptance state."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds", type=Path, default=Path(__file__).parents[1] / "config/foi"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate_catalogue_phase(build_reviewed_catalogue(args.seeds))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
