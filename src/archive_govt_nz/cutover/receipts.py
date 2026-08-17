"""Release cutover receipt data structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CutoverPackageItem:
    """Declared package published under cutover."""

    platform: str
    identifier: str
    sha256: str
    status: str = "verified"

    def to_dict(self) -> dict[str, Any]:
        """Convert item to JSON dictionary."""
        return {
            "platform": self.platform,
            "identifier": self.identifier,
            "sha256": self.sha256,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class ReleaseCutoverReceipt:
    """Evidence certifying production release cutover."""

    receipt_id: str
    executed_at: str
    huggingface_repo: str
    zenodo_concept_doi: str
    fixity_root_sha256: str
    packages_published: tuple[CutoverPackageItem, ...]
    status: str = "completed"

    def to_dict(self) -> dict[str, Any]:
        """Convert receipt to JSON dictionary."""
        return {
            "receipt_id": self.receipt_id,
            "executed_at": self.executed_at,
            "huggingface_repo": self.huggingface_repo,
            "zenodo_concept_doi": self.zenodo_concept_doi,
            "fixity_root_sha256": self.fixity_root_sha256,
            "packages_published": [p.to_dict() for p in self.packages_published],
            "status": self.status,
        }
