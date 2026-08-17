"""RIOPA export receipt data structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RiopaExportReceipt:
    """Evidence documenting RIOPA export generation and schema compliance."""

    receipt_id: str
    exported_at: str
    riopa_spec_version: str
    target_corpus: str
    export_formats: tuple[str, ...]
    records_exported: int
    boundary_integrity_verified: bool
    status: str = "exported"

    def to_dict(self) -> dict[str, Any]:
        """Convert receipt to JSON dictionary."""
        return {
            "receipt_id": self.receipt_id,
            "exported_at": self.exported_at,
            "riopa_spec_version": self.riopa_spec_version,
            "target_corpus": self.target_corpus,
            "export_formats": list(self.export_formats),
            "records_exported": self.records_exported,
            "boundary_integrity_verified": self.boundary_integrity_verified,
            "status": self.status,
        }
