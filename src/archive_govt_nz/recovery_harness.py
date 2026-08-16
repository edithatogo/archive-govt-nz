"""Disaster recovery and backup restore rehearsal harness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from archive_govt_nz.object_store import ObjectStoreError

if TYPE_CHECKING:
    from archive_govt_nz.core.manifests import PreservationManifest
    from archive_govt_nz.object_store import ContentAddressedStore


@dataclass(frozen=True, slots=True)
class RecoveryRehearsalReceipt:
    """Outcome of a disaster recovery rehearsal."""

    manifest_id: str
    records_checked: int
    bytes_recovered: int
    all_fixity_passed: bool
    status: str


class RestoreRehearsalHarness:
    """Automated tool for testing end-to-end disaster recovery and fixity integrity."""

    @classmethod
    def rehearse_recovery(
        cls,
        manifest: PreservationManifest,
        backup_store: ContentAddressedStore,
        target_store: ContentAddressedStore,
    ) -> RecoveryRehearsalReceipt:
        """Simulate disaster recovery: restore objects from backup to target store."""
        records_checked = 0
        bytes_recovered = 0
        all_passed = True

        for record in manifest.records:
            records_checked += 1
            object_id = f"sha256:{record.sha256}"
            try:
                backup_receipt = backup_store.verify(object_id)
                if backup_receipt.sha256 != record.sha256:
                    all_passed = False
                    continue

                raw_bytes = backup_receipt.path.read_bytes()
                target_receipt = target_store.put_bytes(raw_bytes)
                if target_receipt.sha256 != record.sha256:
                    all_passed = False
                    continue

                bytes_recovered += len(raw_bytes)
            except ObjectStoreError, OSError:
                all_passed = False

        status = (
            "passed"
            if all_passed and records_checked == manifest.records_count
            else "failed"
        )
        return RecoveryRehearsalReceipt(
            manifest_id=manifest.manifest_id,
            records_checked=records_checked,
            bytes_recovered=bytes_recovered,
            all_fixity_passed=all_passed,
            status=status,
        )
