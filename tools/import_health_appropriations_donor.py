"""Import and inventory the pinned health-appropriations donor."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import cast

from archive_govt_nz.domains.health_appropriations.donor import (
    import_donor_snapshot,
    verify_donor_reconstruction,
)
from archive_govt_nz.domains.health_appropriations.formats import (
    inventory_pdf,
    inventory_sqlite,
    inventory_workbook,
)
from archive_govt_nz.object_store import ContentAddressedStore

_COMMIT = "4668e6c3b1b492086941d4c1ef96e299250a8301"
_TREE = "c6d44ff79eda73cfc6ba7db5764e27ce01b890e1"
_ARCHIVE = "9c8ab0feaa752ead08163463a634623d55a62a69608772b73127b3d7b709157e"


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix="health-")
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
    """Run the pinned import and write external manifests atomically."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor-root", required=True, type=Path)
    parser.add_argument("--store-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--format-census", required=True, type=Path)
    arguments = parser.parse_args()
    store = ContentAddressedStore(arguments.store_root)
    manifest = import_donor_snapshot(
        arguments.donor_root,
        store,
        expected_commit=_COMMIT,
        expected_tree=_TREE,
        expected_archive_sha256=_ARCHIVE,
        expected_file_count=23,
        expected_total_bytes=6_604_301,
    )
    verify_donor_reconstruction(manifest, store)
    rows = cast("list[dict[str, object]]", manifest["objects"])
    census: list[dict[str, object]] = []
    for row in rows:
        relative = Path(cast("str", row["path"]))
        source = arguments.donor_root / relative
        if source.suffix.lower() == ".xlsx":
            details = inventory_workbook(source)
        elif source.suffix.lower() == ".pdf":
            details = inventory_pdf(source)
        elif source.suffix.lower() == ".sqlite":
            details = inventory_sqlite(source)
        else:
            continue
        census.append(
            {"path": relative.as_posix(), "object_id": row["object_id"], **details}
        )
    _atomic_json(arguments.manifest, manifest)
    _atomic_json(
        arguments.format_census,
        {"schema_version": "archive-govt-nz.health-format-census/v1", "items": census},
    )
    print(
        json.dumps(
            {
                "status": "passed",
                "file_count": manifest["file_count"],
                "format_items": len(census),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
