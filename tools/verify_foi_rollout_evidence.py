"""Verify that rollout rows point at existing, non-promotional evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.foi_rollout_evidence import verify_rollout


def main() -> int:
    """Run the rollout integrity check and emit JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rollout", type=Path)
    parser.add_argument("evidence_dir", type=Path)
    arguments = parser.parse_args()
    report = verify_rollout(arguments.rollout, arguments.evidence_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
