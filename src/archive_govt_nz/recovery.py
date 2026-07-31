"""Idempotency and recovery checks across the ledger and object store."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from archive_govt_nz.ledger import Ledger
from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreError


@dataclass(frozen=True, slots=True)
class RecoveryReport:
    """Bounded reconciliation result."""

    verified_objects: int
    missing_objects: tuple[str, ...]
    corrupt_objects: tuple[str, ...]
    orphan_paths: tuple[str, ...]


def reconcile_objects(ledger: Ledger, root: Path) -> RecoveryReport:
    """Verify ledger object rows and report missing/corrupt/orphan payloads."""
    store = ContentAddressedStore(root)
    rows = ledger.connection.execute(
        "SELECT object_id FROM objects ORDER BY object_id"
    ).fetchall()
    verified = 0
    missing: list[str] = []
    corrupt: list[str] = []
    for row in rows:
        object_id = str(row["object_id"])
        try:
            store.verify(object_id)
        except ObjectStoreError as error:
            if error.error_class == "object_missing":
                missing.append(object_id)
            else:
                corrupt.append(object_id)
        else:
            verified += 1
    referenced = {
        str(row["object_id"])[7:]
        for row in rows
        if str(row["object_id"]).startswith("sha256:")
    }
    orphan_paths = tuple(
        str(path.relative_to(root))
        for path in (root / "sha256").rglob("*")
        if path.is_file() and path.name not in referenced
    )
    return RecoveryReport(verified, tuple(missing), tuple(corrupt), orphan_paths)
