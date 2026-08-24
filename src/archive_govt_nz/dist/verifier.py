"""Cryptographic fixity and manifest verifier for distribution bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from archive_govt_nz.dist.packaging import (
    compute_bundle_root_digest,
    compute_file_fixity,
)

if TYPE_CHECKING:
    from archive_govt_nz.dist.packaging import PublicationManifest


@dataclass(frozen=True, slots=True)
class FixityVerificationReport:
    """Outcome of bundle cryptographic verification."""

    manifest_id: str
    is_valid: bool
    items_checked: int
    items_passed: int
    errors: list[str]


class PublicationVerifier:
    """Verifies local or downloaded release bundles against a PublicationManifest."""

    def verify_manifest_integrity(
        self, manifest: PublicationManifest
    ) -> FixityVerificationReport:
        """Verify the internal structural integrity and root digest of a manifest."""
        errors: list[str] = []
        expected_root = compute_bundle_root_digest(manifest.items)
        if manifest.bundle_root_sha256 != expected_root:
            errors.append(
                f"bundle_root_sha256 mismatch: expected {expected_root}, got {manifest.bundle_root_sha256}"
            )

        return FixityVerificationReport(
            manifest_id=manifest.manifest_id,
            is_valid=len(errors) == 0,
            items_checked=len(manifest.items),
            items_passed=len(manifest.items) if not errors else 0,
            errors=errors,
        )

    def verify_local_files(
        self,
        manifest: PublicationManifest,
        base_dir: Path,
    ) -> FixityVerificationReport:
        """Verify local bundle files on disk against hashes declared in the manifest."""
        errors: list[str] = []
        passed = 0

        for item in manifest.items:
            file_path = base_dir / item.item_path
            if not file_path.exists():
                errors.append(f"Missing file: {item.item_path}")
                continue

            sha256, blake3, size = compute_file_fixity(file_path)
            if sha256 != item.sha256:
                errors.append(
                    f"SHA256 mismatch for {item.item_path}: expected {item.sha256}, got {sha256}"
                )
            elif blake3 != item.blake3:
                errors.append(
                    f"BLAKE3 mismatch for {item.item_path}: expected {item.blake3}, got {blake3}"
                )
            elif size != item.size_bytes:
                errors.append(
                    f"Size mismatch for {item.item_path}: expected {item.size_bytes}, got {size}"
                )
            else:
                passed += 1

        return FixityVerificationReport(
            manifest_id=manifest.manifest_id,
            is_valid=len(errors) == 0,
            items_checked=len(manifest.items),
            items_passed=passed,
            errors=errors,
        )
