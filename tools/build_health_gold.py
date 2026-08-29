"""Build and checksum donor-parity Gold products from Silver."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

from archive_govt_nz.domains.health_appropriations.gold import (
    build_gold_analytics,
    rebuild_compatibility_sqlite,
    render_donor_plots,
)


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix="gold-")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    """Build every Gold artifact and atomically record its digest."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--facts", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    database = args.output_dir / "health_funding_nz.sqlite"
    counts = rebuild_compatibility_sqlite(args.facts, database)
    analytics = build_gold_analytics(args.facts, args.output_dir / "analytics")
    plots = render_donor_plots(args.output_dir / "analytics", args.output_dir / "plots")
    paths = sorted(path for path in args.output_dir.rglob("*") if path.is_file())
    result = {
        "schema_version": "archive-govt-nz.health-gold-manifest/v1",
        "source_facts_sha256": _digest(args.facts),
        "compatibility_table_counts": counts,
        "analytics": analytics,
        "plot_contract": plots,
        "artifacts": [
            {
                "path": path.relative_to(args.output_dir).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _digest(path),
            }
            for path in paths
        ],
    }
    _write(args.manifest, result)
    print(json.dumps({"status": "passed", "artifacts": len(paths)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
