"""Common dispatch for the exact donor parity SQLite snapshot."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from typing import Any

from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    FieldLineage,
    LossAccounting,
    preserved_only,
)
from archive_govt_nz.domains.health_appropriations.donor_sqlite import read_snapshot
from archive_govt_nz.domains.health_appropriations.silver import extract_donor_rows

SOURCE_SHA256 = "a2f9973846e1213823b499e4a019d314485110e80e4ee5a8984ebf3f35c85c8e"
PROFILE = "donor-sqlite-parity/v1"


@dataclass(frozen=True, slots=True)
class DonorSQLiteContext:
    """Explicit observation context, with no new rights decision."""

    observation_id: str
    observed_at: str


@dataclass(frozen=True, slots=True)
class DonorSQLiteAdapter:
    """Reuse the fixed five-table admission and native parity projection."""

    context: DonorSQLiteContext

    def _parse(self, bronze: bytes) -> dict[str, tuple[tuple[Any, ...], ...]] | None:
        try:
            return read_snapshot(bronze, SOURCE_SHA256)
        except ValueError, sqlite3.Error:
            return None

    def matches_layout(self, bronze: bytes) -> bool:
        """Select only the exact pinned donor snapshot and existing table schema."""
        return self._parse(bronze) is not None

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Preserve donor literals and parity semantics without source promotion."""
        if hashlib.sha256(bronze).hexdigest() != source_sha256:
            message = "source_hash_mismatch"
            raise ValueError(message)
        snapshot = self._parse(bronze)
        if snapshot is None:
            return preserved_only(
                source_coordinate="bronze:sha256:" + source_sha256,
                reason="unsupported_donor_sqlite_layout",
            )
        records, lineage, counts = extract_donor_rows(
            snapshot,
            source_sha256=source_sha256,
            observation_id=self.context.observation_id,
            observed_at=self.context.observed_at,
        )
        links = tuple(
            FieldLineage(
                record_id=str(row["record_id"]),
                field=str(row["field"]),
                source_coordinate=str(row["source_coordinate"]),
                raw_value=None if row["raw_value"] is None else str(row["raw_value"]),
                normalized_value=None
                if row["normalized_value"] is None
                else str(row["normalized_value"]),
                rule=str(row["rule"]),
            )
            for row in lineage
        )
        losses = tuple(
            LossAccounting(
                source_coordinate="table:" + table,
                disposition="partially_normalized",
                reason="donor_derivative_rows_and_raw_values_retained",
            )
            for table in sorted(counts)
        )
        return AdapterOutput(tuple(records), losses, links, PROFILE)


def donor_sqlite_registration(context: DonorSQLiteContext) -> AdapterRegistration:
    """Register one closed donor source; observations remain caller-supplied."""
    adapter = DonorSQLiteAdapter(context)
    return AdapterRegistration(
        adapter_id="nz-health-donor-sqlite-parity",
        version="v1",
        media_type="application/vnd.sqlite3",
        adapter=adapter,
        layout_probe=adapter.matches_layout,
    )
