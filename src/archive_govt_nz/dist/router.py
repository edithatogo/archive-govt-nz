"""Multi-target publication router orchestrating remote dataset depositions."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from archive_govt_nz.dist.packaging import PublicationManifest

RECEIPT_SCHEMA: Final[str] = "archive-govt-nz.publication-receipt/v1"


@dataclass(frozen=True, slots=True)
class PublicationReceipt:
    """Standardized publication outcome receipt across all targets."""

    schema_version: str
    receipt_id: str
    target_platform: str
    remote_identifier: str
    published_at: str
    sha256_bundle_root: str
    file_count: int
    total_bytes: int
    status: str
    doi: str | None = None
    commit_pinned_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert receipt to dictionary."""
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "target_platform": self.target_platform,
            "remote_identifier": self.remote_identifier,
            "published_at": self.published_at,
            "sha256_bundle_root": self.sha256_bundle_root,
            "file_count": self.file_count,
            "total_bytes": self.total_bytes,
            "status": self.status,
            "doi": self.doi,
            "commit_pinned_url": self.commit_pinned_url,
        }


class PublicationRouter:
    """Plan target releases without fabricating external publication evidence."""

    CREDENTIAL_ENV_VARS: Final[dict[str, str]] = {
        "huggingface": "HF_TOKEN",
        "zenodo": "ZENODO_TOKEN",
        "osf": "OSF_TOKEN",
        "github_releases": "GITHUB_TOKEN",
    }

    def check_preflight_credentials(
        self, manifest: PublicationManifest
    ) -> dict[str, bool]:
        """Check presence of required environment tokens without exposing secrets."""
        results: dict[str, bool] = {}
        for p in manifest.platforms:
            if not p.enabled:
                continue
            env_var = self.CREDENTIAL_ENV_VARS.get(p.platform)
            has_creds = bool(env_var and os.environ.get(env_var))
            results[p.platform] = has_creds
        return results

    def publish_manifest(
        self,
        manifest: PublicationManifest,
        *,
        dry_run: bool = True,
    ) -> list[PublicationReceipt]:
        """Plan enabled targets; refuse live receipts without a remote transport."""
        receipts: list[PublicationReceipt] = []
        now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        total_bytes = sum(item.size_bytes for item in manifest.items)
        file_count = len(manifest.items)

        for p in manifest.platforms:
            if not p.enabled:
                continue

            receipt_id = f"rcpt-{p.platform}-{manifest.manifest_id}"

            # This legacy router does not call a remote publisher. Authentication
            # presence cannot establish upload, a DOI, or a remotely verified revision.
            receipt = PublicationReceipt(
                schema_version=RECEIPT_SCHEMA,
                receipt_id=receipt_id,
                target_platform=p.platform,
                remote_identifier=p.target_identifier,
                published_at=now_iso,
                sha256_bundle_root=manifest.bundle_root_sha256,
                file_count=file_count if dry_run else 0,
                total_bytes=total_bytes if dry_run else 0,
                status="dry_run" if dry_run else "failed",
            )
            receipts.append(receipt)

        return receipts
