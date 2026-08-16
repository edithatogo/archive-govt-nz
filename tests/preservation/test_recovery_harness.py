"""Test suite for RestoreRehearsalHarness."""

from __future__ import annotations

from typing import TYPE_CHECKING

from archive_govt_nz.core.manifests import PreservationManifest, PreservationRecord
from archive_govt_nz.object_store import ContentAddressedStore
from archive_govt_nz.recovery_harness import RestoreRehearsalHarness

if TYPE_CHECKING:
    from pathlib import Path


def test_rehearse_recovery_success(tmp_path: Path) -> None:
    """Validate full disaster recovery simulation succeeds."""
    backup_store = ContentAddressedStore(tmp_path / "backup_store")
    target_store = ContentAddressedStore(tmp_path / "target_store")

    payload1 = b"Preserved Record 1"
    payload2 = b"Preserved Record 2"
    r1 = backup_store.put_bytes(payload1)
    r2 = backup_store.put_bytes(payload2)

    rec1 = PreservationRecord(
        record_id="rec-1",
        sha256=r1.sha256,
        size_bytes=r1.byte_count,
        media_type="text/plain",
    )
    rec2 = PreservationRecord(
        record_id="rec-2",
        sha256=r2.sha256,
        size_bytes=r2.byte_count,
        media_type="text/plain",
    )

    manifest = PreservationManifest(
        manifest_id="pres-test-001",
        source_id="feed:moh:news",
        sha256_root="0000000000000000000000000000000000000000000000000000000000000000",
        records=(rec1, rec2),
    )

    rehearsal = RestoreRehearsalHarness.rehearse_recovery(
        manifest=manifest,
        backup_store=backup_store,
        target_store=target_store,
    )

    assert rehearsal.status == "passed"
    assert rehearsal.all_fixity_passed is True
    assert rehearsal.records_checked == 2
    assert rehearsal.bytes_recovered == len(payload1) + len(payload2)

    # Verify target store now actually has the objects
    assert target_store.verify(f"sha256:{r1.sha256}").sha256 == r1.sha256
    assert target_store.verify(f"sha256:{r2.sha256}").sha256 == r2.sha256
