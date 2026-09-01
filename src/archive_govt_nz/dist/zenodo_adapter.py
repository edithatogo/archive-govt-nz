"""Zenodo open-science repository distribution adapter."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from archive_govt_nz.dist.packaging import PublicationManifest


@dataclass(frozen=True, slots=True)
class ZenodoDepositionOutcome:
    """Outcome of a Zenodo deposition creation and publishing operation."""

    deposition_id: str | None
    doi: str | None
    title: str
    files_uploaded: int
    bytes_uploaded: int
    status: str
    error_message: str | None = None


class ZenodoDistributionAdapter:
    """Creates versioned open-access depositions on Zenodo with DOI assignment."""

    def __init__(self, token: str | None = None) -> None:
        """Initialize adapter with explicit token or environment ZENODO_TOKEN."""
        self.token = token or os.environ.get("ZENODO_TOKEN")

    def publish_deposition(
        self,
        manifest: PublicationManifest,
        target_deposition_id: str | None = None,
        *,
        dry_run: bool = True,
    ) -> ZenodoDepositionOutcome:
        """Publish publication manifest bundle to Zenodo."""
        _ = target_deposition_id
        if dry_run:
            return ZenodoDepositionOutcome(
                deposition_id=None,
                doi=None,
                title=manifest.bundle_name,
                files_uploaded=0,
                bytes_uploaded=0,
                status="prepared-not-published",
            )

        if not self.token:
            return ZenodoDepositionOutcome(
                deposition_id=None,
                doi=None,
                title=manifest.bundle_name,
                files_uploaded=0,
                bytes_uploaded=0,
                status="failed",
                error_message=(
                    "ZENODO_TOKEN environment variable or explicit token is missing"
                ),
            )

        return ZenodoDepositionOutcome(
            deposition_id=None,
            doi=None,
            title=manifest.bundle_name,
            files_uploaded=0,
            bytes_uploaded=0,
            status="failed",
            error_message=(
                "remote Zenodo deposition is not implemented; use the gated "
                "ZenodoClient workflow"
            ),
        )
