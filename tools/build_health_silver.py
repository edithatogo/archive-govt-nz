"""Build donor-parity Silver Parquet from the verified Bronze object."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import cast

from archive_govt_nz.domains.health_appropriations.silver import (
    normalize_donor_sqlite,
)
from archive_govt_nz.object_store import ContentAddressedStore


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix="silver-")
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
    """Resolve the donor SQLite object, normalize it, and pin every output."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor-manifest", type=Path, required=True)
    parser.add_argument("--store-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--observed-at", required=True)
    args = parser.parse_args()
    donor = json.loads(args.donor_manifest.read_text(encoding="utf-8"))
    objects = cast("list[dict[str, object]]", donor["objects"])
    row = next(
        item
        for item in objects
        if item["path"] == "data/processed/health_funding_nz.sqlite"
    )
    store = ContentAddressedStore(args.store_root, create=False)
    receipt = store.verify(cast("str", row["object_id"]))
    result = normalize_donor_sqlite(
        receipt.path,
        args.output_dir,
        source_sha256=receipt.sha256,
        observation_id="donor-4668e6c-sqlite",
        observed_at=args.observed_at,
    )
    result["source_object_id"] = receipt.object_id
    result["output_sha256"] = {
        name: _digest(args.output_dir / name)
        for name in cast("list[str]", result["outputs"])
    }
    _write(args.manifest, result)
    print(json.dumps({"status": "passed", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
