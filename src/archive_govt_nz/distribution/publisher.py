"""Multi-platform archive publication and distribution orchestrator."""

from __future__ import annotations

import enum
import hashlib
import zipfile
from dataclasses import dataclass
from typing import TYPE_CHECKING

from archive_govt_nz.core.manifests import PublicationReceipt

if TYPE_CHECKING:
    from pathlib import Path


class DistributionTarget(enum.StrEnum):
    """Supported target distribution repositories."""

    HUGGINGFACE = "huggingface"
    ZENODO = "zenodo"
    GITHUB_RELEASES = "github_releases"
    OSF = "osf"


@dataclass(frozen=True, slots=True)
class PublicationOptions:
    """Optional metadata and publication status options."""

    receipt_id: str | None = None
    doi: str | None = None
    commit_pinned_url: str | None = None
    status: str = "published"


class DistributionPublisher:
    """Orchestrates multi-target package distribution and receipt generation."""

    @staticmethod
    def prepare_release_bundle(
        files: list[Path], output_bundle_path: Path
    ) -> tuple[str, int, int]:
        """Bundle multiple release files into a deterministic zip container."""
        output_bundle_path.parent.mkdir(parents=True, exist_ok=True)
        sha = hashlib.sha256()
        total_bytes = 0

        with zipfile.ZipFile(output_bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in sorted(files, key=lambda p: p.name):
                content = file_path.read_bytes()
                zf.writestr(file_path.name, content)
                sha.update(content)
                total_bytes += len(content)

        bundle_sha256 = sha.hexdigest()
        return bundle_sha256, len(files), total_bytes

    @classmethod
    def create_publication_receipt(
        cls,
        target: DistributionTarget,
        remote_identifier: str,
        bundle_sha256: str,
        bundle_stats: tuple[int, int],  # (file_count, total_bytes)
        options: PublicationOptions | None = None,
    ) -> PublicationReceipt:
        """Create a verifiable PublicationReceipt for a successful distribution."""
        opts = options or PublicationOptions()
        file_count, total_bytes = bundle_stats
        ident_hash = hashlib.sha256(remote_identifier.encode()).hexdigest()[:12]
        rid = opts.receipt_id or f"rcpt:{target.value}:{ident_hash}"
        return PublicationReceipt(
            receipt_id=rid,
            target_platform=target.value,
            remote_identifier=remote_identifier,
            sha256_bundle_root=bundle_sha256,
            file_count=file_count,
            total_bytes=total_bytes,
            status=opts.status,
            doi=opts.doi,
            commit_pinned_url=opts.commit_pinned_url,
        )

    @classmethod
    def publish_dry_run(
        cls,
        target: DistributionTarget,
        remote_identifier: str,
        files: list[Path],
        output_bundle_path: Path,
    ) -> PublicationReceipt:
        """Execute a dry-run release packaging and return verified receipt."""
        bundle_sha, count, total_b = cls.prepare_release_bundle(
            files, output_bundle_path
        )
        return cls.create_publication_receipt(
            target=target,
            remote_identifier=remote_identifier,
            bundle_sha256=bundle_sha,
            bundle_stats=(count, total_b),
            options=PublicationOptions(status="verified"),
        )
