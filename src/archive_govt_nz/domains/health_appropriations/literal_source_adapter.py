"""Five closed physical sources compose the seven reviewed literal profiles."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations import literal_packages as packages
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    FieldLineage,
    LossAccounting,
    preserved_only,
)
from archive_govt_nz.domains.health_appropriations.fiscal_crown_literals import (
    SOURCE_URL,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    source_context,
    verified_payload,
)

AREA_COORDINATE_PREFIX = "literal-area-json/v1:"


@dataclass(frozen=True, slots=True)
class LiteralBundle:
    """One physical identity always includes every reviewed profile for it."""

    adapter_id: str
    source_sha256: str
    source_locator: str
    source_vintage: str
    profiles: tuple[str, ...]
    max_bytes: int


BUNDLES = (
    LiteralBundle(
        "nz-treasury-befu-2025-detail-literals",
        packages.DETAIL_PROFILES["BEFU-2025"][0],
        "data/raw/befu25-data-expense-tables.xlsx",
        "BEFU-2025",
        ("befu-detail",),
        1024 * 1024,
    ),
    LiteralBundle(
        "nz-treasury-hyefu-2024-detail-literals",
        packages.DETAIL_PROFILES["HYEFU-2024"][0],
        "data/raw/hyefu24-data-expense-tables.xlsx",
        "HYEFU-2024",
        ("hyefu-detail",),
        1024 * 1024,
    ),
    LiteralBundle(
        "nz-treasury-befu-2025-chart-literals",
        packages.befu_chart.SOURCE_SHA256,
        "data/raw/befu25-charts-data.xlsx",
        "BEFU-2025",
        ("befu-chart", "befu-residual"),
        4 * 1024 * 1024,
    ),
    LiteralBundle(
        "nz-treasury-hyefu-2024-chart-literals",
        packages.allowance.SOURCE_SHA256,
        "data/raw/hyefu24-charts-data.xlsx",
        "HYEFU-2024",
        ("hyefu-allowance", "hyefu-residual"),
        4 * 1024 * 1024,
    ),
    LiteralBundle(
        "nz-treasury-fiscal-2025-crown-literals",
        packages.SOURCE_SHA256,
        SOURCE_URL,
        packages.PROFILES["crown"],
        ("crown",),
        1024 * 1024,
    ),
)


@dataclass(frozen=True, slots=True)
class LiteralSourceAdapter:
    """Exact-source selection, shared admission and lossless native projection."""

    bundle: LiteralBundle
    observed_at: str

    def matches_layout(self, bronze: bytes) -> bool:
        """Pin layout by reviewed byte identity; recheck admission on extraction."""
        return (
            0 < len(bronze) <= self.bundle.max_bytes
            and hashlib.sha256(bronze).hexdigest() == self.bundle.source_sha256
        )

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Retain native profile facts, JSON context and profile-scoped areas."""
        verified_payload(bronze, source_sha256, max_bytes=self.bundle.max_bytes)
        if not self.matches_layout(bronze):
            return preserved_only(
                source_coordinate="bronze:sha256:" + source_sha256,
                reason="unsupported_literal_source_layout",
            )
        records, lineage, losses = [], [], []
        try:
            for profile in self.bundle.profiles:
                context = {
                    "source_object_sha256": source_sha256,
                    "source_locator": self.bundle.source_locator,
                    "source_vintage": self.bundle.source_vintage,
                    "observed_at": self.observed_at,
                }
                admission, context = packages.admit_literal_snapshot(
                    bronze, profile=profile, context=context
                )
                facts, links, areas, _ = packages.project_literal_admission(
                    admission, profile=profile, context=context
                )
                records.extend(
                    pa.Table.from_pylist(facts, schema=packages.FACT_SCHEMA).to_pylist()
                )
                lineage.extend(
                    FieldLineage(
                        record_id=row["record_id"],
                        field=row["field"],
                        source_coordinate=row["source_coordinate"],
                        raw_value=row["raw_value_json"],
                        normalized_value=row["raw_value_json"],
                        rule="literal_source_json_preserved/v1",
                    )
                    for row in links
                )
                # Retain the complete native location/exception/record descriptor
                # in this new source-specific coordinate format. No global
                # protocol field or existing native output changes.
                losses.extend(
                    LossAccounting(
                        source_coordinate=AREA_COORDINATE_PREFIX
                        + encode_json({"profile": profile, **row}),
                        disposition=row["state"],
                        reason=row["reason"],
                    )
                    for row in areas
                )
        except ValueError, TypeError, KeyError, IndexError, OSError, pa.ArrowException:
            return preserved_only(
                source_coordinate="bronze:sha256:" + source_sha256,
                reason="reviewed_literal_admission_failed",
            )
        return AdapterOutput(
            tuple(records),
            tuple(losses),
            tuple(lineage),
            self.bundle.adapter_id + "/v1",
        )


def literal_source_registration(
    *, source_locator: str, source_vintage: str, observed_at: str
) -> AdapterRegistration:
    """Register one exact bundle without omitting sibling source profiles."""
    matches = [
        s
        for s in BUNDLES
        if (s.source_locator, s.source_vintage) == (source_locator, source_vintage)
    ]
    if len(matches) != 1:
        message = "unsupported_literal_source_context"
        raise ValueError(message)
    spec = matches[0]
    source_context(spec.source_sha256, source_locator, source_vintage, observed_at)
    adapter = LiteralSourceAdapter(spec, observed_at)
    return AdapterRegistration(
        adapter_id=spec.adapter_id,
        version="v1",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        adapter=adapter,
        layout_probe=adapter.matches_layout,
    )
