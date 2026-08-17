"""Release cutover coordination and continuity validation."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from archive_govt_nz.cutover.receipts import (
    CutoverPackageItem,
    ReleaseCutoverReceipt,
)

if TYPE_CHECKING:
    from pathlib import Path


class CutoverOrchestrator:
    """Coordinates release cutover and continuity receipts."""

    @classmethod
    def coordinate_release_cutover(
        cls,
        huggingface_repo: str,
        zenodo_concept_doi: str,
        package_files: list[Path],
        receipt_id: str | None = None,
    ) -> ReleaseCutoverReceipt:
        """Execute cutover packaging and generate publication receipt."""
        root_sha = hashlib.sha256()
        packages: list[CutoverPackageItem] = []

        for p_file in sorted(package_files, key=lambda f: f.name):
            data = p_file.read_bytes()
            f_sha = hashlib.sha256(data).hexdigest()
            root_sha.update(f_sha.encode())
            packages.append(
                CutoverPackageItem(
                    platform="huggingface",
                    identifier=f"{huggingface_repo}:{p_file.name}",
                    sha256=f_sha,
                )
            )

        # Add Zenodo concept item
        zenodo_sha = hashlib.sha256(zenodo_concept_doi.encode()).hexdigest()
        packages.append(
            CutoverPackageItem(
                platform="zenodo",
                identifier=zenodo_concept_doi,
                sha256=zenodo_sha,
            )
        )

        now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        rid = receipt_id or f"cutover:release-{int(datetime.now(UTC).timestamp())}"

        return ReleaseCutoverReceipt(
            receipt_id=rid,
            executed_at=now_iso,
            huggingface_repo=huggingface_repo,
            zenodo_concept_doi=zenodo_concept_doi,
            fixity_root_sha256=root_sha.hexdigest(),
            packages_published=tuple(packages),
            status="completed",
        )
