"""Closed Fiscal 2024 common dispatch sharing the native historical extractor."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import cast
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations import historical
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    FieldLineage,
    LossAccounting,
    preserved_only,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    source_context,
    verified_payload,
)

SOURCE_SHA256 = "769f2e7dd6000878cd29c2d913ad6979f28c5391c971292e6abf6148e83eb32d"
SOURCE_LOCATOR = "data/raw/fiscaltimeseries1972-2024.xlsx"
VINTAGE = "fiscal-2024"
MAX_BYTES = 64 * 1024 * 1024
CELL_COORDINATE_PREFIX = "historical-cell-json/v1:"
SHEET_COORDINATE_PREFIX = "historical-sheet-json/v1:"
ADAPTER_ID = "nz-treasury-fiscal-2024-historical-health-gdp"


@dataclass(frozen=True, slots=True)
class HistoricalSourceAdapter:
    """Pin one reviewed source and preserve native loss descriptors in full."""

    observed_at: str

    def matches_layout(self, bronze: bytes) -> bool:
        """Select exact reviewed bytes; extraction reruns bounded admission."""
        return (
            0 < len(bronze) <= MAX_BYTES
            and hashlib.sha256(bronze).hexdigest() == SOURCE_SHA256
        )

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Return native typed rows, lineage and all cell/sheet dispositions."""
        verified_payload(bronze, source_sha256, max_bytes=MAX_BYTES)
        if not self.matches_layout(bronze):
            return preserved_only(
                source_coordinate="bronze:sha256:" + source_sha256,
                reason="unsupported_historical_source_layout",
            )
        try:
            tables, manifest = historical.extract_historical_snapshot(
                bronze,
                expected_sha256=source_sha256,
                source_locator=SOURCE_LOCATOR,
                source_vintage=VINTAGE,
                observed_at=self.observed_at,
            )
            records = tuple(tables["historical_facts.parquet"].to_pylist())
            lineage = tuple(
                FieldLineage(
                    record_id=row["record_id"],
                    field=row["field"],
                    source_coordinate=row["source_coordinate"],
                    raw_value=row["raw_value"],
                    normalized_value=row["normalized_value"],
                    rule=row["rule"],
                )
                for row in tables["field_lineage.parquet"].to_pylist()
            )
            losses = [
                LossAccounting(
                    source_coordinate=CELL_COORDINATE_PREFIX + encode_json(row),
                    disposition=row["disposition"],
                    reason=row["reason"],
                )
                for row in tables["cell_dispositions.parquet"].to_pylist()
            ]
            excluded = cast("list[dict[str, str]]", manifest["excluded_sheets"])
            losses.extend(
                LossAccounting(
                    source_coordinate=SHEET_COORDINATE_PREFIX
                    + encode_json({"source_object_sha256": source_sha256, **row}),
                    disposition="preserved_only",
                    reason=row["reason"],
                )
                for row in excluded
            )
        except (
            BadZipFile,
            ParseError,
            ValueError,
            TypeError,
            KeyError,
            IndexError,
            OSError,
            pa.ArrowException,
        ):
            return preserved_only(
                source_coordinate="bronze:sha256:" + source_sha256,
                reason="reviewed_historical_admission_failed",
            )
        return AdapterOutput(records, tuple(losses), lineage, ADAPTER_ID + "/v1")


def historical_source_registration(
    *, source_locator: str, source_vintage: str, observed_at: str
) -> AdapterRegistration:
    """Register one exact historical context without rights or vintage inference."""
    if (source_locator, source_vintage) != (SOURCE_LOCATOR, VINTAGE):
        message = "unsupported_historical_source_context"
        raise ValueError(message)
    source_context(SOURCE_SHA256, source_locator, source_vintage, observed_at)
    adapter = HistoricalSourceAdapter(observed_at)
    return AdapterRegistration(
        adapter_id=ADAPTER_ID,
        version="v1",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        adapter=adapter,
        layout_probe=adapter.matches_layout,
    )
