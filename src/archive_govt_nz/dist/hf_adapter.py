"""Legacy HF planning adapter; live publication fails until real transport is wired."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from archive_govt_nz.dist.packaging import PublicationManifest


@dataclass(frozen=True, slots=True)
class HFSyncOutcome:
    """Outcome of a Hugging Face repository synchronization operation."""

    repository: str
    branch: str
    commit_sha: str | None
    files_synced: int
    bytes_synced: int
    status: str
    error_message: str | None = None


class HuggingFaceDistributionAdapter:
    """Synchronizes Parquet tables and dataset metadata to Hugging Face Hub."""

    def __init__(self, token: str | None = None) -> None:
        """Initialize adapter with explicit token or environment variable HF_TOKEN."""
        self.token = token or os.environ.get("HF_TOKEN")

    def sync_manifest(
        self,
        manifest: PublicationManifest,  # noqa: ARG002 - preserve disabled API keyword
        target_repository: str,
        *,
        branch: str = "main",
        dry_run: bool = True,
    ) -> HFSyncOutcome:
        """Synchronize dataset release bundle to target HF repository."""
        if dry_run:
            return HFSyncOutcome(
                repository=target_repository,
                branch=branch,
                commit_sha=None,
                files_synced=0,
                bytes_synced=0,
                status="dry_run",
            )

        if not self.token:
            return HFSyncOutcome(
                repository=target_repository,
                branch=branch,
                commit_sha=None,
                files_synced=0,
                bytes_synced=0,
                status="failed",
                error_message="HF_TOKEN or an explicit token is missing",
            )

        return HFSyncOutcome(
            repository=target_repository,
            branch=branch,
            commit_sha=None,
            files_synced=0,
            bytes_synced=0,
            status="failed",
            error_message=(
                "Live upload and anonymous readback are not implemented "
                "in this legacy adapter"
            ),
        )
