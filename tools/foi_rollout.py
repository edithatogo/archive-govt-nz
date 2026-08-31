"""Write the every-entity FOI work ledger; never fetch or activate a source."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.foi_discovery import build_reviewed_catalogue
from archive_govt_nz.foi_rollout import build_rollout


def main() -> int:
    """Print deterministic public-safe planning metadata from verified seeds."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds", type=Path, default=Path(__file__).resolve().parents[1] / "config/foi"
    )
    arguments = parser.parse_args()
    print(
        json.dumps(build_rollout(build_reviewed_catalogue(arguments.seeds)), indent=2)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
