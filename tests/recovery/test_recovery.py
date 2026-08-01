"""Recovery and idempotency contracts."""

from pathlib import Path

from archive_govt_nz.ledger import Ledger
from archive_govt_nz.object_store import ContentAddressedStore
from archive_govt_nz.recovery import reconcile_objects


def test_recovery_reconciles_verified_missing_and_orphan_objects(
    tmp_path: Path,
) -> None:
    """A restart distinguishes valid, missing, and unreferenced payloads."""
    object_root = tmp_path / "objects"
    store = ContentAddressedStore(object_root)
    receipt = store.put_bytes(b"valid")
    orphan = store.put_bytes(b"orphan")
    corrupt = store.put_bytes(b"corrupt")
    corrupt.path.write_bytes(b"changed")
    ledger = Ledger(tmp_path / "ledger.sqlite")
    ledger.record_object(
        receipt.object_id, receipt.sha256, receipt.blake3, receipt.byte_count, "source"
    )
    ledger.record_object(
        corrupt.object_id,
        corrupt.sha256,
        corrupt.blake3,
        corrupt.byte_count,
        "source",
    )
    missing = "sha256:" + "a" * 64
    ledger.record_object(missing, "a" * 64, "b" * 64, 1, "source")
    report = reconcile_objects(ledger, object_root)
    assert report.verified_objects == 1
    assert report.missing_objects == (missing,)
    assert report.corrupt_objects == (corrupt.object_id,)
    assert any(orphan.sha256 in item for item in report.orphan_paths)
    ledger.close()
